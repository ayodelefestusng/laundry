"""
Resilient ordered migration: SQLite → PostgreSQL
Respects FK dependency order. Skips signals. Saves checkpoint every record.
Re-run anytime to resume from last checkpoint.
"""
import json, os, time, sys, django
from django.apps import apps
from django.db import transaction
from django.db.models.signals import (
    post_save, pre_save, m2m_changed, post_delete, pre_delete
)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

CHECKPOINT = 'migration_checkpoint.json'

def load_done():
    if os.path.exists(CHECKPOINT):
        try:
            return set(json.load(open(CHECKPOINT)))
        except: pass
    return set()

def save_done(done):
    with open(CHECKPOINT, 'w') as f:
        json.dump(list(done), f)

def disable_signals():
    for sig in [pre_save, post_save, pre_delete, post_delete, m2m_changed]:
        sig.receivers = []

def get_all(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

# Ordered load sequence — each group only after its dependencies are done
MODEL_ORDER = [
    # Group 0: No FK deps
    'myapp.state',
    'myapp.servicecategory',
    'auth.group',
    # Group 1: Depends on State
    'myapp.town',
    # Group 2: Depends on Town (optionally)
    'myapp.tenant',
    'myapp.premiumclient',
    # Group 3: Depends on Tenant, Town, State  
    'myapp.customuser',
    # Group 4: Depends on Tenant, CustomUser
    'myapp.cluster',
    'myapp.color',
    'myapp.package',
    'myapp.servicechoices',
    'myapp.deliveryprice',
    'myapp.tenantattribute',
    # Group 5: Depends on the above
    'myapp.order',
    'myapp.orderitem',
    'myapp.payment',
    'myapp.comment',
    'myapp.qr',
    'myapp.workflowstage',
    'myapp.workflowinstance',
    'myapp.workflowhistory',
    'myapp.workflowrecord',
]

def get_lookup(model_name, entry):
    fields = entry.get('fields', {})
    pk = entry.get('pk')
    if pk is not None:
        return {'pk': pk}
    if model_name == 'auth.group':
        return {'name': fields['name']}
    if model_name == 'myapp.customuser':
        return {'email': fields['email']}
    if 'name' in fields:
        return {'name': fields['name']}
    return None

def try_insert(Model, lookup, processed_fields, max_retries=3, wait=2):
    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                obj, created = Model.objects.update_or_create(
                    **lookup, defaults=processed_fields
                )
            return True
        except Exception as e:
            print(f'    ↻ Retry {attempt+1}/{max_retries}: {e}', flush=True)
            time.sleep(wait)
    return False

def load_model(all_data, model_name, done):
    entries = [e for e in all_data if e['model'] == model_name]
    if not entries:
        return done, 0
    
    Model = apps.get_model(model_name)
    loaded = 0
    print(f'\n[{model_name}] {len(entries)} records', flush=True)

    for idx, entry in enumerate(entries):
        rid = f"{model_name}::{entry.get('pk', 'npk')}::{idx}"
        if rid in done:
            continue

        fields = entry.get('fields', {})
        lookup = get_lookup(model_name, entry)
        if not lookup:
            done.add(rid)
            continue

        # Build non-M2M fields
        processed = {}
        for f_name, f_val in fields.items():
            try:
                field_obj = Model._meta.get_field(f_name)
                if field_obj.many_to_many:
                    continue
                if field_obj.is_relation:
                    if f_val is not None and not isinstance(f_val, list):
                        processed[f_name + '_id'] = f_val
                else:
                    processed[f_name] = f_val
            except Exception:
                continue

        print(f'  [{idx+1}/{len(entries)}] {lookup} ... ', end='', flush=True)
        ok = try_insert(Model, lookup, processed)
        if ok:
            print('✓', flush=True)
            loaded += 1
        else:
            print('✗ SKIPPED', flush=True)

        done.add(rid)
        save_done(done)

    return done, loaded

def main():
    disable_signals()
    done = load_done()

    print(f'Checkpoint: {len(done)} records already migrated.\n')

    # Load all source data
    all_data = []
    for fname in ['data_groups.json', 'data_myapp.json', 'data_auth.json']:
        if os.path.exists(fname):
            all_data.extend(get_all(fname))
    
    total_loaded = 0
    for model_name in MODEL_ORDER:
        done, n = load_model(all_data, model_name, done)
        total_loaded += n

    # Load any remaining models not in ORDER list
    seen_models = set(MODEL_ORDER)
    remaining = set(e['model'] for e in all_data) - seen_models
    for model_name in sorted(remaining):
        done, n = load_model(all_data, model_name, done)
        total_loaded += n

    print(f'\n✅ Migration complete. {total_loaded} new records inserted.')
    if os.path.exists(CHECKPOINT):
        os.remove(CHECKPOINT)

if __name__ == '__main__':
    main()
