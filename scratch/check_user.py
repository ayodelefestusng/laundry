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
    user = CustomUser.objects.get(email=email)
    print(f"User found: {user.email}, is_staff: {user.is_staff}, tenant: {user.tenant}")
    if user.tenant:
        print(f"Tenant: {user.tenant.name}, subdomain: {user.tenant.subdomain}")
except CustomUser.DoesNotExist:
    print(f"User {email} NOT found.")

try:
    tenant = Tenant.objects.get(email=email)
    print(f"Tenant found with email: {tenant.name}, subdomain: {tenant.subdomain}")
except Tenant.DoesNotExist:
    print(f"Tenant with email {email} NOT found.")
