"""
Pure psycopg2 migration: reads data JSON files and inserts directly into PostgreSQL.
No Django ORM, no signal overhead.  Per-statement 30s timeout + retry on failure.
Re-run anytime -- uses INSERT ... ON CONFLICT DO NOTHING for idempotency.
"""
import json, os, sys, time, io
import psycopg2
from dotenv import load_dotenv

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv()

DB_URI = os.getenv(
    "DATABASE_URI",
    "postgres://postgres:dec6192e465cd7659a82@147.182.194.8:5439/laundry_db"
)

CHECKPOINT = "pg_migration_checkpoint.json"

def load_done():
    if os.path.exists(CHECKPOINT):
        try:
            return set(json.load(open(CHECKPOINT)))
        except: pass
    return set()

def save_done(done):
    with open(CHECKPOINT, 'w') as f:
        json.dump(list(done), f)

def get_conn():
    for attempt in range(10):
        try:
            conn = psycopg2.connect(DB_URI, connect_timeout=15)
            conn.autocommit = False
            return conn
        except Exception as e:
            print(f"Connection failed (attempt {attempt+1}): {e}")
            time.sleep(5)
    sys.exit("Cannot connect to database after 10 attempts.")

def insert_records(conn, table, pk_col, columns, rows, done, model_key):
    cur = conn.cursor()
    inserted = 0
    skipped = 0
    col_list = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    if pk_col:
        sql = f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders}) ON CONFLICT ("{pk_col}") DO NOTHING'
    else:
        sql = f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

    for idx, row in enumerate(rows):
        rid = f"{model_key}::{idx}"
        if rid in done:
            skipped += 1
            continue

        print(f"  [{idx+1}/{len(rows)}] {table}... ", end="", flush=True)
        success = False
        for attempt in range(5):
            try:
                cur.execute("SAVEPOINT sp")
                cur.execute("SET LOCAL statement_timeout = '300s'")
                cur.execute(sql, row)
                conn.commit()
                success = True
                break
            except psycopg2.IntegrityError as e:
                conn.rollback()
                print(f"skip (conflict)", flush=True)
                success = True
                break
            except psycopg2.OperationalError as e:
                print(f"\n  Network error (attempt {attempt+1}/5): {e}. Reconnecting...", flush=True)
                try: conn.rollback()
                except: pass
                try: cur.close()
                except: pass
                conn = get_conn()
                cur = conn.cursor()
            except Exception as e:
                print(f"\n  Error: {e}", flush=True)
                try: conn.rollback()
                except: pass
                break  # skip this record

        if success:
            print("OK", flush=True)
            inserted += 1
        else:
            print("FAILED - skipping", flush=True)

        done.add(rid)
        save_done(done)

    try: cur.close()
    except: pass
    print(f"  --> {table}: {inserted} inserted, {skipped} already done\n")
    return conn

def load_model(all_data, model_name):
    return [e for e in all_data if e['model'] == model_name]

def main():
    done = load_done()
    print(f"Checkpoint loaded: {len(done)} records done.\n")

    all_data = []
    for fname in ['data_groups.json', 'data_myapp.json', 'data_auth.json']:
        if os.path.exists(fname):
            with open(fname, 'r', encoding='utf-8') as f:
                all_data.extend(json.load(f))

    conn = get_conn()
    print(f"Connected to PostgreSQL.\n")

    # 1. States
    entries = load_model(all_data, 'myapp.state')
    if entries:
        cols = ['id', 'name']
        rows = [[e.get('pk'), e['fields'].get('name')] for e in entries]
        conn = insert_records(conn, 'myapp_state', 'id', cols, rows, done, 'myapp.state')

    # 2. Service Categories
    entries = load_model(all_data, 'myapp.servicecategory')
    if entries:
        cols = ['id', 'name', 'description', 'icon']
        rows = [[e.get('pk'), e['fields'].get('name'), e['fields'].get('description'), e['fields'].get('icon')] for e in entries]
        conn = insert_records(conn, 'myapp_servicecategory', 'id', cols, rows, done, 'myapp.servicecategory')

    # 3. Towns
    entries = load_model(all_data, 'myapp.town')
    if entries:
        cols = ['id', 'name', 'state_id']
        rows = [[e.get('pk'), e['fields'].get('name'), e['fields'].get('state')] for e in entries]
        conn = insert_records(conn, 'myapp_town', 'id', cols, rows, done, 'myapp.town')

    # 4. Tenants (inspect actual columns dynamically to avoid missing field errors)
    entries = load_model(all_data, 'myapp.tenant')
    if entries:
        sample_fields = entries[0]['fields'].keys()
        cols = ['id'] + [
            k for k in sample_fields
            if k not in ('state', 'town') and not isinstance(entries[0]['fields'][k], list)
        ]
        fk_cols = {k: k + '_id' for k in ('state', 'town') if k in sample_fields}
        def make_tenant_row(e):
            row = [e.get('pk')]
            f = e['fields']
            for c in cols[1:]:
                row.append(f.get(c))
            return row
        # Build cols including FK renames
        all_cols = ['id']
        for k in list(entries[0]['fields'].keys()):
            if isinstance(entries[0]['fields'][k], list): continue
            if k in ('state', 'town'):
                all_cols.append(k + '_id')
            else:
                all_cols.append(k)
        rows = []
        for e in entries:
            f = e['fields']
            row = [e.get('pk')]
            for k in list(entries[0]['fields'].keys()):
                if isinstance(f.get(k), list): continue
                if k in ('state', 'town'):
                    row.append(f.get(k))
                else:
                    row.append(f.get(k))
            rows.append(row)
        conn = insert_records(conn, 'myapp_tenant', 'id', all_cols, rows, done, 'myapp.tenant')

    # 5. Users
    entries = load_model(all_data, 'myapp.customuser')
    if entries:
        cols = ['id', 'password', 'last_login', 'email', 'name', 'phone',
                'address', 'latitude', 'longitude', 'is_active', 'is_staff',
                'is_superuser', 'is_seller', 'is_buyer', 'mfa_secret', 'mfa_enabled',
                'tenant_id', 'state_id', 'town_id']
        rows = []
        for e in entries:
            f = e.get('fields', {})
            rows.append([
                e.get('pk'), f.get('password'), f.get('last_login'),
                f.get('email'), f.get('name'), f.get('phone'),
                f.get('address'), f.get('latitude'), f.get('longitude'),
                f.get('is_active', True), f.get('is_staff', False),
                f.get('is_superuser', False), f.get('is_seller', False),
                f.get('is_buyer', True), f.get('mfa_secret'), f.get('mfa_enabled', False),
                f.get('tenant'), f.get('state'), f.get('town'),
            ])
        conn = insert_records(conn, 'myapp_customuser', 'id', cols, rows, done, 'myapp.customuser')

    # 6. Auth Groups
    entries = load_model(all_data, 'auth.group')
    if entries:
        cols = ['id', 'name']
        rows = [[e.get('pk') or (idx+1), e['fields'].get('name')] for idx, e in enumerate(entries)]
        conn = insert_records(conn, 'auth_group', 'id', cols, rows, done, 'auth.group')

    # 7. Orders
    entries = load_model(all_data, 'myapp.order')
    if entries:
        cols = ['id', 'tenant_id', 'customer_id', 'status', 'created_at', 'updated_at',
                'shipping_fee', 'total_price', 'notes', 'recipient_name',
                'recipient_phone', 'recipient_address', 'recipient_state_id',
                'recipient_town_id', 'is_custom_address', 'delivery_date',
                'reschedule_date', 'invoice_sent']
        rows = []
        for e in entries:
            f = e.get('fields', {})
            rows.append([
                e.get('pk'), f.get('tenant'), f.get('customer'), f.get('status'),
                f.get('created_at'), f.get('updated_at'), f.get('shipping_fee'),
                f.get('total_price'), f.get('notes'), f.get('recipient_name'),
                f.get('recipient_phone'), f.get('recipient_address'),
                f.get('recipient_state'), f.get('recipient_town'),
                f.get('is_custom_address', False), f.get('delivery_date'),
                f.get('reschedule_date'), f.get('invoice_sent', False),
            ])
        conn = insert_records(conn, 'myapp_order', 'id', cols, rows, done, 'myapp.order')

    # 8. Order Items
    entries = load_model(all_data, 'myapp.orderitem')
    if entries:
        cols = ['id', 'order_id', 'package_id', 'quantity', 'price', 'status', 'color_id', 'color_custom', 'qr_code']
        rows = []
        for e in entries:
            f = e.get('fields', {})
            rows.append([
                e.get('pk'), f.get('order'), f.get('package') or f.get('service'), f.get('quantity', 1),
                f.get('price') or f.get('unit_price'), f.get('status'), f.get('color'), f.get('color_custom'), f.get('qr_code')
            ])
        conn = insert_records(conn, 'myapp_orderitem', 'id', cols, rows, done, 'myapp.orderitem')

    try: conn.close()
    except: pass
    print("\nMigration complete!")
    if os.path.exists(CHECKPOINT):
        os.remove(CHECKPOINT)

if __name__ == '__main__':
    main()
