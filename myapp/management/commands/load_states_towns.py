import json
import codecs
import sys
from django.core.management.base import BaseCommand
from myapp.models import State, Town

class Command(BaseCommand):
    help = 'Loads states and towns from states_towns.json and aligns PKs alphabetically'

    def handle(self, *args, **kwargs):
        file_path = 'states_towns.json'
        try:
            with codecs.open(file_path, 'r', 'utf-16') as f:
                content = f.read()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to read file: {e}"))
            return
            
        # Clean up 'HomeView\r\n' prefix if it exists
        if content.startswith('HomeView'):
            content = content.partition('\n')[2].strip()
            
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Failed to parse JSON: {e}"))
            return

        # Prepare extraction logic
        states_temp = {}
        towns_temp = []

        for item in data:
            model_type = item.get("model")
            fields = item.get("fields", {})
            pk = item.get("pk")
            
            if model_type == "buyrite.state":
                states_temp[pk] = fields.get("name")
            elif model_type in ["buyrite.town", "buyrite.lga", "buyrite.localgovernment"]:
                # The state field could be 'state' referencing the state PK
                towns_temp.append({
                    "name": fields.get("name"),
                    "state_pk": fields.get("state")
                })
        
        if not states_temp:
            self.stdout.write(self.style.ERROR("No states found in JSON."))
            return

        self.stdout.write(self.style.WARNING("Clearing existing States and Towns..."))
        Town.objects.all().delete()
        State.objects.all().delete()

        # Sort states alphabetically
        sorted_states = sorted(states_temp.values())
        state_objects = []
        state_mapping = {}  # Map 'old state PK' to 'new State object'
        
        self.stdout.write(f"Creating {len(sorted_states)} States alphabetically...")
        for name in sorted_states:
            # Find the original PK to link towns later
            old_pk = next(k for k, v in states_temp.items() if v == name)
            state_obj = State.objects.create(name=name)
            state_mapping[old_pk] = state_obj
            
        # Process towns
        self.stdout.write(f"Creating {len(towns_temp)} Towns alphabetically...")
        # Sort towns alphabetically
        sorted_towns = sorted(towns_temp, key=lambda t: t['name'])
        
        for t_info in sorted_towns:
            state_obj = state_mapping.get(t_info['state_pk'])
            if state_obj:
                Town.objects.create(name=t_info['name'], state=state_obj)
        
        self.stdout.write(self.style.SUCCESS("Successfully loaded states and towns with alphabetical PKs!"))
