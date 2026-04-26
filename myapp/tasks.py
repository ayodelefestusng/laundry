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
            try:
                tenant = Tenant.objects.get(pk=tenant_id)
                if hasattr(tenant, 'attribute') and tenant.attribute.brand_name:
                    brand_name = tenant.attribute.brand_name
            except Tenant.DoesNotExist:
                pass
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
                # from_header = tenant.vectra_email
                # if hasattr(tenant, 'attribute') and tenant.attribute.brand_name:
                #     from_header = f"{tenant.attribute.brand_name} <{tenant.vectra_email}>"
                    
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
            connection=custom_connection,
            # ADD THESE HEADERS
            headers={
                'Message-ID': f'<{uuid.uuid4()}@{settings.EMAIL_HOST}>',
                'Date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z'),
                'X-Priority': '3 (Normal)',
                'X-Mailer': 'Vectra-Dashboard-Mailer'
            }
        )

        if html_content:
            msg.attach_alternative(html_content, "text/html")

        msg.send()
        
        logger.info(f"✅ Email sent successfully from: {from_header}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}", exc_info=True)
        return False

@shared_task
def send_email_async4(subject, text_content, html_content, to_emails, from_email=None, tenant_id=None):
    """
    Asynchronously sends an email using Celery, optionally with tenant-specific SMTP credentials.
    """
    from django.conf import settings
    from django.core.mail import EmailMultiAlternatives, get_connection
    from myapp.models import Tenant

    
    
    
    logger.info(f"Attempting to send email to {to_emails} with subject '{subject}', tenant_id: {tenant_id}")

    
    # Store for logging
    _tenant_vectra = None
    _tenant_pass = None

    custom_connection = None
    # 1. Determine the sender address (Start with default)
    sender_to_use = from_email or settings.DEFAULT_FROM_EMAIL
    
    

    # 2. Handle Tenant Logic
    if tenant_id:
        try:
            tenant = Tenant.objects.get(pk=tenant_id)
            logger.info(f"Retrieved tenant {tenant_id} - Code: {tenant.code}")

            # Create connection if credentials exist
            if tenant.vectra_email and tenant.password:
                logger.info(f"🔧 Creating CUSTOM connection for tenant {tenant_id}")
                custom_connection = get_connection(
                    host=settings.EMAIL_HOST,
                    port=settings.EMAIL_PORT,
                    username=tenant.vectra_email,
                    password=tenant.password,
                    use_tls=settings.EMAIL_USE_TLS,
                    use_ssl=settings.EMAIL_USE_SSL
                )

                _tenant_pass = tenant.password

                # Override sender to the tenant's specific email
                sender_to_use = tenant.vectra_email

            # Apply Brand Name if available
            if hasattr(tenant, 'attribute') and tenant.attribute.brand_name:
                sender_to_use = f"{tenant.attribute.brand_name} <{sender_to_use}>"
            
            logger.info(f"✅ Sender configured as: {sender_to_use}")

        except Tenant.DoesNotExist:
            logger.warning(f"Tenant {tenant_id} not found.")

    # 3. Send the Email
    try:
        logger.info(
            f"📧 Email Connection Details for tenant {tenant_id}: "
            f"host={settings.EMAIL_HOST}, port={settings.EMAIL_PORT}, "
            f"username={sender_to_use}, "
            f"password={_tenant_pass}, "
            f"ssl={settings.EMAIL_USE_SSL}, tls={settings.EMAIL_USE_TLS}, "
            f"from_email={sender_to_use}"
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=sender_to_use,
            to=to_emails,
            connection=custom_connection,
        )

        if html_content:
            msg.attach_alternative(html_content, "text/html")

        msg.send()
        
        log_type = "tenant SMTP" if custom_connection else "fallback backend"
        logger.info(f"✅ Email sent successfully via {log_type} from: {sender_to_use}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_emails}: {e}", exc_info=True)
        return False

@shared_task
def send_email_async3(subject, text_content, html_content, to_emails, from_email=None, tenant_id=None):
    """
    Asynchronously sends an email using Celery, optionally with tenant-specific SMTP credentials.
    """
    try:
        logger.info(f"Attempting to send email to {to_emails} with subject '{subject}', tenant_id: {tenant_id}, from_email: {from_email}")
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives, get_connection
        from myapp.models import Tenant

        custom_connection = None
        # Default sender
        sender_email = from_email or settings.DEFAULT_FROM_EMAIL
        
        
        # default_from_email = settings.DEFAULT_FROM_EMAIL
        # Start with the default from_email
        # final_from_email = from_email or settings.DEFAULT_FROM_EMAIL

        # Store tenant info for logging outside the if block
        _tenant_vectra = None
        _tenant_pass = None

        if tenant_id:
            try:
                tenant = Tenant.objects.get(pk=tenant_id)
                tenant_email_info = f"Tenant {tenant_id} - Tenant Code: {tenant.code}, Veactra Email: {tenant.vectra_email}, Main Email: {tenant.email}, Password: {'Yes' if tenant.password else 'No'}"
                logger.info(f"Retrieved tenant email info: {tenant_email_info}")
                
                # Store for logging
                _tenant_vectra = tenant.vectra_email
                _tenant_pass = tenant.password
                
                # Check if tenant has custom email credentials
                if tenant.vectra_email and tenant.password:
                    logger.info(f"🔧 Creating CUSTOM connection for tenant {tenant_id}: host={settings.EMAIL_HOST}, port={settings.EMAIL_PORT}, username={tenant.vectra_email}, use_ssl={settings.EMAIL_USE_SSL}, use_tls={settings.EMAIL_USE_TLS}")
                    custom_connection = get_connection(
                        host=settings.EMAIL_HOST,
                        port=settings.EMAIL_PORT,
                        username=tenant.vectra_email, # Authenticating as tenant
                        password=tenant.password,
                        use_tls=settings.EMAIL_USE_TLS,
                        use_ssl=settings.EMAIL_USE_SSL
                    )
                    # Use tenant's email as sender, fallback to default
                    # from_email = tenant.vectra_email if tenant.vectra_email else settings.EMAIL_HOST_USER
                    
                    
                    
                    # CRITICAL FIX: Match from_email to the authenticated user
                    # final_from_email = tenant.vectra_email
                    # FIX: Force the sender to match the authenticated user
                    sender_email = tenant.vectra_email
                    logger.info(f"✅ Using tenant email as sender: {sender_email}")
                    logger.info(f"✅ Custom connection CREATED for tenant {tenant_id} (auth: {tenant.vectra_email}, sender: {sender_email})")
                else:
                    logger.info(f"⚠️ Tenant {tenant_id} has NO custom SMTP credentials (vectra_email={tenant.vectra_email}, password_set={bool(tenant.password)})")
                
                logger.info(f"Custom email connection for tenant {tenant_id}: {'Yes' if custom_connection else 'No'}, Username: {settings.EMAIL_HOST_USER}")
                # Check if tenant has a brand name
                if hasattr(tenant, 'attribute') and tenant.attribute.brand_name:
                    if tenant.vectra_email and tenant.password:
                        final_from_email = f"{tenant.attribute.brand_name} <{tenant.vectra_email}>"
                    else:
                        # Fallback to default email address but use tenant's brand name
                        final_from_email = f"{tenant.attribute.brand_name} <{sender_email}>"

            except Tenant.DoesNotExist:
                logger.warning(f"Tenant {tenant_id} not found when attempting to send email.")
                pass
            
        # from_email = from_email or default_from_email
        # from_email = settings.EMAIL_HOST_USER  # Force using default from_email for consistency in logging and fallback
        # Log connection details for debugging
        logger.info(
            f"📧 Email Connection Details for tenant {tenant_id}: "
            f"host={settings.EMAIL_HOST}, port={settings.EMAIL_PORT}, "
            f"username={_tenant_vectra or settings.EMAIL_HOST_USER}, "
            f"password={_tenant_pass if _tenant_pass else 'None'}, "
            f"ssl={settings.EMAIL_USE_SSL}, tls={settings.EMAIL_USE_TLS}, "
            f"from_email={sender_email}"
        )
        
        try:
            if custom_connection:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=sender_email, # Now matches the auth user
                    to=to_emails,
                    connection=custom_connection,
                )
                if html_content:
                    msg.attach_alternative(html_content, "text/html")
                msg.send()
                logger.info(f"✅ Sent via tenant SMTP {tenant_id}")
                logger.info(f"✅ Email sent successfully using {sender_email}")
                return True
        except Exception as e:
            logger.error(f"❌ Tenant SMTP failed, falling back: {e}", exc_info=True)
    
       
        # fallback to default backend
        logger.info(f"📧 Using FALLBACK connection (no custom tenant SMTP): host={settings.EMAIL_HOST}, port={settings.EMAIL_PORT}, username={settings.EMAIL_HOST_USER}, password={settings.EMAIL_HOST_PASSWORD}, use_ssl={settings.EMAIL_USE_SSL}, use_tls={settings.EMAIL_USE_TLS}")

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=sender_email,
            to=to_emails,
        )  # no custom_connection → uses EMAIL_BACKEND
        if html_content:
            msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info("✅ Sent via fallback backend")
        logger.info(f"📧 Confirmation (no custom tenant SMTP): host={settings.EMAIL_HOST}, port={settings.EMAIL_PORT}, username={settings.EMAIL_HOST_USER}, password={settings.EMAIL_HOST_PASSWORD}, use_ssl={settings.EMAIL_USE_SSL}, use_tls={settings.EMAIL_USE_TLS}")

        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_emails}: {e}", exc_info=True)
        return False


@shared_task
def send_email_async2(subject, text_content, html_content, to_emails, from_email=None, tenant_id=None):
    try:
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives, get_connection
        from myapp.models import Tenant
        import uuid # Add this for uniqueness

        sender_to_use = from_email or settings.DEFAULT_FROM_EMAIL
        custom_connection = None

        if tenant_id:
            try:
                tenant = Tenant.objects.get(pk=tenant_id)
                if tenant.vectra_email and tenant.password:
                    # Create the connection
                    custom_connection = get_connection(
                        host=settings.EMAIL_HOST,
                        port=settings.EMAIL_PORT,
                        username=tenant.vectra_email,
                        password=tenant.password,
                        use_tls=settings.EMAIL_USE_TLS,
                        use_ssl=settings.EMAIL_USE_SSL
                    )
                    sender_to_use = tenant.vectra_email
            except Tenant.DoesNotExist:
                logger.warning(f"Tenant {tenant_id} not found.")

        # USE THE CONTEXT MANAGER HERE
        with (custom_connection or get_connection()) as conn:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=sender_to_use,
                to=to_emails,
                connection=conn,
                headers={'Message-ID': f'<{uuid.uuid4()}@vectra.ng>'} # Helps with filtering
            )
            
            if html_content:
                msg.attach_alternative(html_content, "text/html")
            
            msg.send()
            
        logger.info(f"✅ Email sent successfully from: {sender_to_use}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}", exc_info=True)
        return False  
    

@shared_task
def send_email_async1(subject, text_content, html_content, to_emails, from_email=None, tenant_id=None):
    """
    Asynchronously sends an email using Celery, optionally with tenant-specific SMTP credentials.
    """
    try:
        logger.info(f"Attempting to send email to {to_emails} with subject '{subject}', tenant_id: {tenant_id}, from_email: {from_email}")
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives, get_connection
        from myapp.models import Tenant

        custom_connection = None
        default_from_email = settings.DEFAULT_FROM_EMAIL
        final_from_email = from_email or default_from_email
        if tenant_id:
            try:
                tenant = Tenant.objects.get(pk=tenant_id)
                tenant_email_info = f"Tenant {tenant_id} - Tenant Code: {tenant.code}, Veactra Email: {tenant.vectra_email}, Main Email: {tenant.email}, Password: {'Yes' if tenant.password else 'No'}"
                logger.info(f"Retrieved tenant email info: {tenant_email_info}")
                # Check if tenant has custom email credentials
                if tenant.vectra_email and tenant.password:
                    custom_connection = get_connection(
                        host=settings.EMAIL_HOST,
                        port=settings.EMAIL_PORT,
                        username=tenant.vectra_email,
                        password=tenant.password,
                        #  username=settings.EMAIL_HOST_USER,
                        # password=settings.EMAIL_HOST_PASSWORD,
                        use_tls=settings.EMAIL_USE_TLS,
                        use_ssl=settings.EMAIL_USE_SSL
                    )
                    from_email = tenant.vectra_email
                logger.info(f"Custom email connection for tenant {tenant_id}: {'Yes' if custom_connection else 'No'},Username: {settings.EMAIL_HOST_USER}")
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
        # from_email =  settings.DEFAULT_FROM_EMAIL
        logger.info(f"Detail of  email to {to_emails}: Subject: {subject}, From: {from_email}, To: {to_emails}, Custom Connection Used: {'Yes' if custom_connection else 'No'}, Tenant ID: {tenant_id}")

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
