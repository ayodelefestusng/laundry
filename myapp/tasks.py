from math import log

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_email_async(subject, text_content, html_content, to_emails, from_email=None, tenant_id=None):
    """
    Asynchronously sends an email using Celery, optionally with tenant-specific SMTP credentials.
    """
    try:
        logger.info(f"Attempting to send email to {to_emails} with subject '{subject}'")
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives, get_connection
        from myapp.models import Tenant

        custom_connection = None
        default_from_email = settings.DEFAULT_FROM_EMAIL

        if tenant_id:
            try:
                tenant = Tenant.objects.get(pk=tenant_id)
                # Check if tenant has custom email credentials
                if tenant.vectra_email and tenant.password:
                    custom_connection = get_connection(
                        host=settings.EMAIL_HOST,
                        port=settings.EMAIL_PORT,
                        username=tenant.vectra_email,
                        password=tenant.password,
                        use_tls=settings.EMAIL_USE_TLS,
                        use_ssl=settings.EMAIL_USE_SSL
                    )
                
                # Check if tenant has a brand name
                if hasattr(tenant, 'attribute') and tenant.attribute.brand_name:
                    if tenant.vectra_email and tenant.password:
                        default_from_email = f"{tenant.attribute.brand_name} <{tenant.vectra_email}>"
                    else:
                        # Fallback to default email address but use tenant's brand name
                        default_from_email = f"{tenant.attribute.brand_name} <{settings.EMAIL_HOST_USER}>"

            except Tenant.DoesNotExist:
                logger.warning(f"Tenant {tenant_id} not found when attempting to send email.")
                pass

        from_email = from_email or default_from_email
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=to_emails,
            connection=custom_connection,
        )
        if html_content:
            msg.attach_alternative(html_content, "text/html")
            
        msg.send()
        logger.info(f"Successfully sent email to {to_emails}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_emails}: {e}", exc_info=True)
        return False


from celery import shared_task

@shared_task
def add(x, y):
    return x + y



from django.core.mail import send_mail
from celery import shared_task

@shared_task
def send_test_email():
    return send_mail(
        "Test Email",
        "This is a test.",
        "Dignity Concept <upwardwave.dignity@gmail.com>",
        ["ayodelefestusng@gmail.com"],
        fail_silently=False,
    )
