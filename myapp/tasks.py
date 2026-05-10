from math import log

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
import logging
from chromadb import logger
import uuid
from datetime import datetime
# logger = logging.getLogger(__name__)

@shared_task
def send_email_async(subject, text_content, html_content, to_emails, from_email=None, tenant_id=None):
    from django.conf import settings
    from django.core.mail import EmailMultiAlternatives, get_connection
    from myapp.models import Tenant

    logger.info(f"Attempting to send email to {to_emails} with subject '{subject}', tenant_id: {tenant_id}")

    custom_connection = None
    # Default values
    smtp_username = settings.EMAIL_HOST_USER
    from_header = from_email or settings.DEFAULT_FROM_EMAIL
    _tenant_pass = "DEFAULT_SYSTEM_PASS"


    brand_name = "Vectra Laundry"  # Default brand name
    if tenant_id:
        try:
            tenant = Tenant.objects.get(pk=tenant_id)
            if hasattr(tenant, 'attribute') and tenant.attribute.brand_name:
                brand_name = tenant.attribute.brand_name
            
            from_header = f"{brand_name} <{smtp_username}>"
            
            if tenant.vectra_email and tenant.password:
                logger.info(f"🔧 Creating CUSTOM connection for tenant {tenant_id}")
                
                # 1. AUTHENTICATION: Use the raw email only
                smtp_username = tenant.vectra_email
                _tenant_pass = tenant.password
                
                custom_connection = get_connection(
                    host=settings.EMAIL_HOST,
                    port=settings.EMAIL_PORT,
                    username=smtp_username, 
                    password=_tenant_pass,
                    use_tls=settings.EMAIL_USE_TLS,
                    use_ssl=settings.EMAIL_USE_SSL
                )
                
                # 2. DISPLAY: Format the header with brand name
                from_header = f"{brand_name} <{tenant.vectra_email}>"
        except Tenant.DoesNotExist:
            logger.warning(f"Tenant {tenant_id} not found.")

    # 3. Send the Email
    try:
        logger.info(f"📧 Sending as: {from_header} (Auth User: {smtp_username}) password: {_tenant_pass}")
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_header, # Formatted display name
            to=to_emails,
            connection=custom_connection
        )

        if html_content:
            msg.attach_alternative(html_content, "text/html")

        msg.send()
        
        logger.info(f"✅ Email sent successfully from: {from_header}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}", exc_info=True)
        return False



from celery import shared_task

@shared_task
def add(x, y):
    return x + y



from django.core.mail import send_mail
from celery import shared_task

@shared_task
def send_test_email():
    """
    Test task to validate send_email_async via Celery.
    """
    subject = "Celery Validation Test Using Send Test Email Function"
    text_content = "This is a test email sent via Celery using send_email_async."
    html_content = "<p>This is a <b>test email</b> sent via Celery using send_email_async.</p>"
    to_emails = ["ayodelefestusng@gmail.com"]
    
    return send_email_async(subject, text_content, html_content, to_emails)



from django.core.mail import send_mail
from celery import shared_task

@shared_task
def send_test_email1():
    return send_mail(
        subject="Test Email",
        message="This is a test email with fallback.",
        from_email=None,  # backend sets automatically
        recipient_list=["buyriteautosng@gmail.com"],
    )


    
    

# myapp/tasks.py
from celery import shared_task
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

@shared_task(name="myapp.tasks.send_power_email")
def send_power_email(status, device_time, server_time):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    to_email = os.getenv("ALERT_RECIPIENT")

    subject = f"ALERT: Grid Power is {status.upper()}"
    body = (
        f"Grid Status: {status.upper()}\n"
        f"Server Event Time: {server_time}\n"
        f"Device Uptime (ms): {device_time}\n"
        f"Location: Ikorodu Node"
    )

    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        logger.info(f"Email sent successfully for status: {status}")
    except Exception as e:
        logger.error(f"Email failed in worker: {e}")
        # Celery best practice: wrap in try-except to prevent worker crash