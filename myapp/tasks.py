from math import log

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_email_async(subject, text_content, html_content, to_emails, from_email=None):
    """
    Asynchronously sends an email using Celery.
    """
    try:
        logger.info(f"Attempting to send email to {to_emails} with subject '{subject}'")
        from django.conf import settings
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=to_emails,
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
