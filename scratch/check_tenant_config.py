import os
import django
import sys

# Add the project directory to sys.path
sys.path.append(r'c:\Users\Pro\Desktop\PROJECT\Laundry\myproject')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from myapp.models import CustomUser, Tenant

email = 'buyriteautosng@gmail.com'
try:
    tenant = Tenant.objects.get(email=email)
    print(f"Tenant: {tenant.name}")
    print(f"Vectra Email: {tenant.vectra_email}")
    print(f"Has Password: {bool(tenant.password)}")
except Tenant.DoesNotExist:
    print(f"Tenant with email {email} NOT found.")
