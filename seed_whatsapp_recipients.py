"""
Seed Script: Set WhatsApp recipients on all existing Feeder rows.
Run once after applying the pearl_dt_three_phase_fields migration.

Usage (from Laundry/myproject directory):
  python manage.py shell < seed_whatsapp_recipients.py

Or run directly:
  python seed_whatsapp_recipients.py
"""

import os
import django

# Adjust if your settings module path differs
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from myapp.models import Feeder

WHATSAPP_PRIMARY = "2348021299221"
WHATSAPP_GROUP   = "120363410539285836@g.us"

updated = 0
for feeder in Feeder.objects.all():
    changed = False
    if not feeder.whatsapp_primary:
        feeder.whatsapp_primary = WHATSAPP_PRIMARY
        changed = True
    if not feeder.whatsapp_group:
        feeder.whatsapp_group = WHATSAPP_GROUP
        changed = True
    if changed:
        feeder.save(update_fields=["whatsapp_primary", "whatsapp_group"])
        updated += 1
        print(f"  Updated: {feeder.name}")

print(f"\nDone. {updated} feeder(s) updated.")
