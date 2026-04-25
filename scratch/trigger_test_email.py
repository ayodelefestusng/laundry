import os
import django
import sys

# Add the project directory to sys.path
sys.path.append(r'c:\Users\Pro\Desktop\PROJECT\Laundry\myproject')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from myapp.tasks import send_test_email

print("Sending test email...")
result = send_test_email.delay()
print(f"Task queued. ID: {result.id}")
