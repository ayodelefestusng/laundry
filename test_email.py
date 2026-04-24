import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from myapp.tasks import send_email_async
from django.core.mail import send_mail

print("Sending test email synchronously...")
try:
    result = send_email_async(
        subject="Test Email Debug",
        text_content="This is a test to see if email sending works.",
        html_content="<p>This is a test.</p>",
        to_emails=["ayodelefestusng@gmail.com"]
    )
    print("Task returned:", result)
except Exception as e:
    print("Exception occurred:")
    import traceback
    traceback.print_exc()
