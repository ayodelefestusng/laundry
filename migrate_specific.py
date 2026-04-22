"""
Migrate specific tables from SQLite to PostgreSQL
Handles FK dependencies properly
"""
import os
import sys

# Set DATABASE_URI before Django setup
os.environ['DATABASE_URI'] = 'postgres://postgres:dec6192e465cd7659a82@147.182.194.8:5439/laundry_db?connect_timeout=60'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

import django
django.setup()

import sqlite3
from psycopg2 import connect
from psycopg2.extras import execute_batch

from django.conf import settings

# Get PostgreSQL connection
def get_pg_connection():
    db_settings = settings.DATABASES['default']
    return connect(
        host=db_settings['HOST'],
        port=db_settings['PORT'],
        dbname=db_settings['NAME'],
        user=db_settings['USER'],
        password=db_settings['PASSWORD']
    )

# Migration order - following FK dependencies
MIGRATION_ORDER = [
    # Step 1: Base tables (no FK deps or only depend on themselves)
    ('myapp_tenant', ['id', 'name', 'code', 'subdomain', 'email', 'phone', 'is_active', 'created_at', 'created_by_id']),
    ('myapp_state', ['id', 'name']),
    ('myapp_town', ['id', 'name', 'state_id']),
    ('myapp_customuser', ['id', 'password', 'last_login', 'is_superuser', 'email', 'name', 'phone', 'is_active', 'is_staff', 'is_seller', 'is_buyer', 'mfa_secret', 'mfa_enabled', 'tenant_id', 'state_id', 'town_id', 'address', 'latitude', 'longitude', 'line_manager_id', 'deputy_person_id']),
    
    # Step 2: Tenant-dependent tables
    ('myapp_servicecategory', ['id', 'tenant_id', 'name']),
    ('myapp_servicechoices', ['id', 'tenant_id', 'name']),
    ('myapp_color', ['id', 'tenant_id', 'name', 'hex_code']),
    
    # Step 3: Cluster (depends on tenant, town)
    ('myapp_cluster', ['id', 'tenant_id', 'name']),
    
    # Step 4: M2M for Cluster-Town
    ('myapp_cluster_towns', ['id', 'cluster_id', 'town_id']),
    
    # Step 5: DeliveryPricing (depends on tenant, cluster)
    ('myapp_deliverypricing', ['id', 'tenant_id', 'cluster_id', 'price']),
    
    # Step 6: Package (depends on tenant, category, service_type)
    ('myapp_package', ['id', 'tenant_id', 'category_id', 'service_type_id', 'price', 'delivery_time_days']),
    
    # Step 7: QR (depends on tenant)
    ('myapp_qr', ['id', 'tenant_id', 'code', 'status']),
]

def convert_boolean(value):
    """Convert integer to boolean for PostgreSQL"""
    return bool(value) if value is not None else None

def migrate_table(table_name, columns):
    """Migrate a single table from SQLite to PostgreSQL"""
    sqlite_path = 'db.sqlite3'
    conn_sqlite = sqlite3.connect(sqlite_path)
    conn_sqlite.row_factory = sqlite3.Row
    cursor_sqlite = conn_sqlite.cursor()
    
    # Get data from SQLite
    cursor_sqlite.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
    rows = cursor_sqlite.fetchall()
    conn_sqlite.close()
    
    if not rows:
        print(f"  ✓ No records to migrate for {table_name}")
        return True
    
    # Process rows - convert booleans
    processed_rows = []
    for row in rows:
        new_row = []
        for col_idx, col in enumerate(columns):
            val = row[col_idx]
            # Convert boolean fields
            if col in ['is_active', 'is_superuser', 'is_staff', 'is_seller', 'is_buyer', 'mfa_enabled']:
                val = convert_boolean(val)
            new_row.append(val)
        processed_rows.append(tuple(new_row))
    
    # Connect to PostgreSQL
    try:
        conn_pg = get_pg_connection()
        pg_cursor = conn_pg.cursor()
        
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        
        execute_batch(pg_cursor, query, processed_rows)
        conn_pg.commit()
        pg_cursor.close()
        conn_pg.close()
        
        print(f"  ✓ Migrated {len(rows)} records to {table_name}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error migrating {table_name}: {e}")
        return False

def migrate_cluster_towns():
    """Special handling for Cluster-Town M2M relationship"""
    sqlite_path = 'db.sqlite3'
    conn_sqlite = sqlite3.connect(sqlite_path)
    conn_sqlite.row_factory = sqlite3.Row
    cursor_sqlite = conn_sqlite.cursor()
    
    # Get the M2M relationship data - check both possible table names
    try:
        cursor_sqlite.execute("SELECT cluster_id, town_id FROM myapp_cluster_towns")
    except:
        cursor_sqlite.execute("SELECT cluster_id, town_id FROM myapp_cluster_towns")
    
    rows = cursor_sqlite.fetchall()
    conn_sqlite.close()
    
    if not rows:
        print(f"  ✓ No cluster_towns records to migrate")
        return True
    
    # Process rows - remove the id column
    processed_rows = []
    for row in rows:
        processed_rows.append((row['cluster_id'], row['town_id']))
    
    try:
        conn_pg = get_pg_connection()
        pg_cursor = conn_pg.cursor()
        
        query = "INSERT INTO myapp_cluster_towns (cluster_id, town_id) VALUES (%s, %s) ON CONFLICT DO NOTHING"
        execute_batch(pg_cursor, query, processed_rows)
        conn_pg.commit()
        pg_cursor.close()
        conn_pg.close()
        
        print(f"  ✓ Migrated {len(rows)} cluster_towns records")
        return True
        
    except Exception as e:
        print(f"  ✗ Error migrating cluster_towns: {e}")
        return False

def main():
    print("=" * 60)
    print("Starting migration from SQLite to PostgreSQL")
    print("=" * 60)
    
    # First migrate the main tables
    for table_name, columns in MIGRATION_ORDER:
        if table_name == 'myapp_cluster_towns':
            continue  # Handle separately
        print(f"\nMigrating {table_name}...")
        migrate_table(table_name, columns)
    
    # Then handle M2M relationship
    print(f"\nMigrating myapp_cluster_towns...")
    migrate_cluster_towns()
    
    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()