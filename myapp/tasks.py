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
import pytz
from datetime import datetime, time, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.utils import timezone

logger = logging.getLogger(__name__)

# Evolution API Credentials for Power Tracker Bot
EVOLUTION_API_URLS = os.getenv("EVOLUTION_API_URL", "https://whatsapp-1-evolution-api.xqqhik.easypanel.host")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "429683C4C977415CAAFCCE10F7D57E11")
POWER_INSTANCE = os.getenv("POWER_INSTANCE", "power_max_bot")

def format_time_dot(dt):
    """
    Format a datetime object to h.mmam/pm in Africa/Lagos timezone (e.g. 5.13am, 12.41pm).
    """
    lagos_tz = pytz.timezone("Africa/Lagos")
    if timezone.is_aware(dt):
        dt = dt.astimezone(lagos_tz)
    else:
        dt = lagos_tz.localize(dt)
    h_12 = dt.strftime("%I")
    minute = dt.strftime("%M")
    ampm = dt.strftime("%p").lower()
    h_12 = str(int(h_12))  # strip leading zero
    return f"{h_12}.{minute}{ampm}"

def format_duration(td):
    """
    Format a timedelta object to Xhr(s) Ymin(s) (e.g. 1hr 23mins, 4hrs 40mins).
    """
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    parts = []
    if hours > 0:
        h_str = "hr" if hours == 1 else "hrs"
        parts.append(f"{hours}{h_str}")
    if minutes > 0 or not parts:
        m_str = "min" if minutes == 1 else "mins"
        parts.append(f"{minutes}{m_str}")
    return " ".join(parts)

def send_whatsapp_power_message(number: str, text: str):
    """
    Send a text message via Evolution API to the specified contact.
    """
    import requests
    url = f"{EVOLUTION_API_URLS}/message/sendText/{POWER_INSTANCE}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    clean_number = number.replace("+", "").strip()
    recipient = f"{clean_number}@s.whatsapp.net" if "@" not in clean_number else clean_number
    
    payload = {
        "number": recipient,
        "text": text,
        "linkPreview": False
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        logger.info(f"WhatsApp power alert sent to {recipient}. Status code: {response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to send WhatsApp power alert to {recipient}: {e}", exc_info=True)
        return None

def generate_power_report(feeder, target_date, is_today=True):
    """
    Query power status updates and reconstruct the power cycles on the target date.
    """
    from myapp.models import PowerStatus
    lagos_tz = pytz.timezone("Africa/Lagos")
    
    start_naive = datetime.combine(target_date, time.min)
    end_naive = datetime.combine(target_date, time.max)
    
    start_dt = timezone.make_aware(start_naive, lagos_tz)
    end_dt = timezone.make_aware(end_naive, lagos_tz)
    
    # Query updates on target date
    updates = list(PowerStatus.objects.filter(
        feeder=feeder,
        server_time__range=(start_dt, end_dt)
    ).order_by('server_time'))
    
    # Query last update before target date to check starting state
    pre_update = PowerStatus.objects.filter(
        feeder=feeder,
        server_time__lt=start_dt
    ).order_by('-server_time').first()
    
    cycles = []
    current_on = None
    
    if pre_update and pre_update.status.upper() == 'ON':
        current_on = start_dt
        
    for u in updates:
        status_upper = u.status.upper()
        if status_upper == 'ON':
            if current_on is None:
                current_on = u.server_time
        elif status_upper == 'OFF':
            if current_on is not None:
                cycles.append((current_on, u.server_time))
                current_on = None
                
    if current_on is not None:
        end_of_cycle = timezone.now().astimezone(lagos_tz) if is_today else end_dt
        cycles.append((current_on, end_of_cycle))
        
    # Format cycles and compute supply duration
    lines = []
    total_supply = timedelta()
    
    date_str = target_date.strftime("%d/%m/%Y")
    day_label = "today" if is_today else "yesterday"
    lines.append(f"{feeder.name} as @ {day_label} {date_str}")
    
    for on_time, off_time in cycles:
        duration = off_time - on_time
        total_supply += duration
        
        on_str = format_time_dot(on_time)
        off_str = format_time_dot(off_time)
        dur_str = format_duration(duration)
        
        lines.append(f"Power on: {on_str}")
        lines.append(f"Power off: {off_str}")
        lines.append(f"Supply {dur_str}")
        
    lines.append("")
    total_supply_str = format_duration(total_supply)
    lines.append(f"Total Supply {total_supply_str}")
    
    if not is_today:
        total_outage = timedelta(hours=24) - total_supply
        if total_outage < timedelta():
            total_outage = timedelta()
        total_outage_str = format_duration(total_outage)
        lines.append(f"Total Outage  {total_outage_str}")
        
    return "\n".join(lines)

@shared_task(name="myapp.tasks.send_power_email")
def send_power_email(feeder_name, status, device_time, server_time, contact_phone=None):
    from myapp.models import Feeder
    
    logger.info(f"Processing real-time power update for Feeder {feeder_name} with status {status}")
    
    # 1. Fetch/Create Feeder
    try:
        feeder, created = Feeder.objects.get_or_create(
            name=feeder_name,
            defaults={"contact_phone": contact_phone}
        )
        if not created and contact_phone and feeder.contact_phone != contact_phone:
            feeder.contact_phone = contact_phone
            feeder.save(update_fields=["contact_phone"])
    except Exception as e:
        logger.error(f"Error retrieving or creating Feeder: {e}", exc_info=True)
        feeder = Feeder(name=feeder_name, contact_phone=contact_phone)

    # 2. Reconstruct today's log cycles report
    try:
        lagos_tz = pytz.timezone("Africa/Lagos")
        today_date = timezone.now().astimezone(lagos_tz).date()
        body = generate_power_report(feeder, today_date, is_today=True)
    except Exception as e:
        logger.error(f"Error generating power report: {e}", exc_info=True)
        body = f"{feeder_name} status is {status}\nServer time: {server_time}"

    # 3. Send Email Alert
    gmail_user = os.getenv("GMAIL_USER") or "upwardwave.dignity@gmail.com"
    gmail_password = os.getenv("GMAIL_APP_PASSWORD") or "ybccjzqmxxlalaal"
    to_email = os.getenv("ALERT_RECIPIENT") or "ayodelefestusng@gmail.com"

    subject = f"ALERT: Grid Power is {status.upper()} - {feeder_name}"

    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        logger.info(f"Power alert email sent successfully to {to_email} for Feeder {feeder_name}")
    except Exception as e:
        logger.error(f"Failed to send email alert for Feeder {feeder_name}: {e}", exc_info=True)

    # 4. Send WhatsApp Alert
    phone_to_use = contact_phone or feeder.contact_phone
    if phone_to_use:
        send_whatsapp_power_message(phone_to_use, body)
    else:
        logger.warning(f"No contact phone available to send WhatsApp message for Feeder {feeder_name}")

@shared_task(name="myapp.tasks.send_daily_power_updates")
def send_daily_power_updates():
    from myapp.models import Feeder
    
    logger.info("Executing periodic daily power summary updates task")
    
    lagos_tz = pytz.timezone("Africa/Lagos")
    yesterday = (timezone.now().astimezone(lagos_tz) - timedelta(days=1)).date()
    
    feeders = Feeder.objects.all()
    if not feeders.exists():
        logger.info("No feeders found in database for daily updates.")
        return
        
    gmail_user = os.getenv("GMAIL_USER") or "upwardwave.dignity@gmail.com"
    gmail_password = os.getenv("GMAIL_APP_PASSWORD") or "ybccjzqmxxlalaal"
    to_email = os.getenv("ALERT_RECIPIENT") or "ayodelefestusng@gmail.com"
    
    for feeder in feeders:
        try:
            body = generate_power_report(feeder, yesterday, is_today=False)
            subject = f"DAILY POWER SUMMARY: {feeder.name} - {yesterday.strftime('%d/%m/%Y')}"
            
            # Send Email
            msg = MIMEMultipart()
            msg['From'] = gmail_user
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(gmail_user, gmail_password)
                    server.sendmail(gmail_user, to_email, msg.as_string())
                logger.info(f"Daily summary email sent for Feeder {feeder.name}")
            except Exception as e:
                logger.error(f"Failed to send daily summary email for Feeder {feeder.name}: {e}", exc_info=True)
                
            # Send WhatsApp
            if feeder.contact_phone:
                send_whatsapp_power_message(feeder.contact_phone, body)
            else:
                logger.info(f"No contact phone available to send daily summary WhatsApp for Feeder {feeder.name}")
                
        except Exception as e:
            logger.error(f"Error generating daily summary report for Feeder {feeder.name}: {e}", exc_info=True)


@shared_task(name="myapp.tasks.send_security_alert_email")
def send_security_alert_email(feeder_name, transformer_name, contact_phone, msisdn, server_time):
    logger.warning(
        f"🚨 SECURITY ALERT: Hardware SIM mismatch detected for Feeder: {feeder_name} "
        f"({transformer_name}). Expected contact: {contact_phone}, received SIM: {msisdn} "
        f"at {server_time}."
    )
    
    # 1. Prepare email content
    gmail_user = os.getenv("GMAIL_USER") or "upwardwave.dignity@gmail.com"
    gmail_password = os.getenv("GMAIL_APP_PASSWORD") or "ybccjzqmxxlalaal"
    to_email = os.getenv("ALERT_RECIPIENT") or "ayodelefestusng@gmail.com"

    subject = f"🚨 SECURITY ALERT: SIM Mismatch for {feeder_name}"
    
    body = (
        f"CRITICAL SECURITY ALERT\n"
        f"=======================\n\n"
        f"A hardware SIM card identity mismatch has been detected on the power tracker network.\n\n"
        f"Feeder Name: {feeder_name}\n"
        f"Transformer: {transformer_name}\n"
        f"Designated Contact: {contact_phone}\n"
        f"Active SIM MSISDN: {msisdn}\n"
        f"Detection Server Time: {server_time}\n\n"
        f"Please verify the hardware node immediately to prevent unauthorized access or tampering."
    )

    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # 2. Send email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        logger.info(f"Security alert email sent successfully to {to_email} for Feeder {feeder_name}")
    except Exception as e:
        logger.error(f"Failed to send security alert email: {e}", exc_info=True)

    # 3. Send WhatsApp message if phone matches or target alert contact
    phone_to_use = contact_phone
    if phone_to_use:
        send_whatsapp_power_message(phone_to_use, body)
    else:
        logger.warning("No contact phone available to send security alert WhatsApp.")