import json
import os
import time
import django
from django.core.management import call_command
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

PROGRESS_FILE = 'migration_progress.json'

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"completed": []}

def save_progress(completed_ids):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({"completed": completed_ids}, f)

def resilient_load(filename):
    print(f"\nStarting resilient load for {filename}...")
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    progress = load_progress()
    completed = set(progress["completed"])

    total = len(data)
    for idx, entry in enumerate(data):
        # Unique ID for tracking: filename + idx (since pk might not be unique across different models in the same file)
        record_id = f"{filename}_{idx}"
        
        if record_id in completed:
            continue

        model = entry.get('model')
        pk = entry.get('pk')
        print(f"[{idx+1}/{total}] Loading {model} (pk={pk})...", end='', flush=True)

        temp_chunk = 'temp_record.json'
        with open(temp_chunk, 'w', encoding='utf-8') as tf:
            json.dump([entry], tf)

        success = False
        retries = 5
        wait = 2
        
        for attempt in range(retries):
            try:
                # Use a small connect_timeout for individual operations if possible
                # But we'll rely on the one in .env
                call_command('loaddata', temp_chunk, verbosity=0)
                success = True
                break
            except Exception as e:
                print(f" (Attempt {attempt+1} failed: {e})", end='', flush=True)
                time.sleep(wait)
                wait *= 2 # Exponential backoff
        
        if success:
            print(" Done.")
            completed.add(record_id)
            save_progress(list(completed))
        else:
            print("\n!!! SHUTTING DOWN: Permanent failure or excessive timeouts. Please check connection and rerun script.")
            return False

    return True

if __name__ == "__main__":
    files = ['data_sites.json', 'data_myapp.json', 'data_auth.json']
    for f in files:
        if os.path.exists(f):
            if not resilient_load(f):
                break
    
    print("\nMigration finished successfully!")
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
