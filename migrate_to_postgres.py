import json
import os
import django
from django.core.management import call_command
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

def load_granular(filename):
    print(f"Loading {filename}...")
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Group by model
    by_model = {}
    for entry in data:
        model = entry['model']
        if model not in by_model:
            by_model[model] = []
        by_model[model].append(entry)
    
    # Load each model separately
    for model, items in by_model.items():
        print(f"  Processing model: {model} ({len(items)} items)")
        chunk_file = f"chunk_{model.replace('.', '_')}.json"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2)
        
        try:
            # We use loaddata on the chunk. 
            # We don't use atomic here because some might fail or hung.
            call_command('loaddata', chunk_file, verbosity=1)
            print(f"    Successfully loaded {model}")
        except Exception as e:
            print(f"    FAILED to load {model}: {e}")
        finally:
            if os.path.exists(chunk_file):
                os.remove(chunk_file)

if __name__ == "__main__":
    for f in ['data_sites.json', 'data_myapp.json', 'data_auth.json']:
        if os.path.exists(f):
            load_granular(f)
