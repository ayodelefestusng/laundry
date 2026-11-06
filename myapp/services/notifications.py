import logging
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from ..models import Incident

logger = logging.getLogger(__name__)

TOKEN_SALT = "incident-admin-approval-v1"
TOKEN_MAX_AGE_SECONDS = 172800  # 48 hours

def generate_approval_token(incident: Incident) -> str:
    """
    Generates a cryptographically signed, timestamped token containing the incident ID.
    """
    signer = TimestampSigner(salt=TOKEN_SALT)
    return signer.sign(str(incident.id))


def decode_approval_token(token: str) -> tuple[int | None, str | None]:
    """
    Validates token integrity and age. Returns (incident_id, error_message).
    """
    signer = TimestampSigner(salt=TOKEN_SALT)
    try:
        incident_id_str = signer.unsign(token, max_age=TOKEN_MAX_AGE_SECONDS)
        return int(incident_id_str), None
    except SignatureExpired:
        logger.warning(f"[Approval Service] Expired approval token presented: {token}")
        return None, "This approval link has expired (validity is 48 hours)."
    except (BadSignature, ValueError) as e:
        logger.error(f"[Approval Service] Invalid token submitted: {token}. Details: {e}")
        return None, "Invalid or corrupted approval link."


def send_admin_approval_request(incident: Incident, request=None) -> bool:
    """
    Dispatches review request to both admin_main and admin_secondary.
    """
    try:
        token = generate_approval_token(incident)
        # Store signature to index/track tokens
        signature_part = token.split(":")[-1]
        incident.approval_token_signature = signature_part
        incident.save(update_fields=['approval_token_signature'])

        path = reverse('incident_action_review', kwargs={'token': token})
        
        # Build absolute URL
        if request:
            action_url = request.build_absolute_uri(path)
        else:
            domain = getattr(settings, 'PORTAL_DOMAIN', 'http://127.0.0.1:8000')
            action_url = f"{domain}{path}"

        subject = f"[Review Required] Incident {incident.tracking_id} - {incident.transformer.name}"
        message = (
            f"An incident was logged on {incident.feeder.name} ({incident.transformer.name}).\n\n"
            f"Tracking ID: {incident.tracking_id}\n"
            f"Type: {incident.get_incident_type_display()}\n"
            f"Reported Date: {incident.incident_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Description: {incident.custom_description or 'None provided'}\n\n"
            f"Please verify and process this report here:\n{action_url}\n\n"
            f"Note: This link is valid for 48 hours."
        )

        recipients = [incident.transformer.admin_main, incident.transformer.admin_secondary]
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False
        )
        logger.info(f"[Approval Service] Review request sent for {incident.tracking_id} to {recipients}")
        return True

    except Exception as e:
        logger.error(f"[Approval Service] Failed to send approval email for {incident.tracking_id}: {e}", exc_info=True)
        return False


def send_user_status_update(incident: Incident) -> bool:
    """
    Notifies the reporting user of the approval/rejection outcome.
    """
    try:
        subject = f"Incident Report Update: {incident.tracking_id} [{incident.get_approval_display()}]"
        
        if incident.approval == 'APPROVED':
            body = (
                f"Your incident report ({incident.tracking_id}) has been APPROVED.\n"
                f"Status: Work in Progress.\n"
                f"Our engineering team has been dispatched to {incident.transformer.name}."
            )
        else:
            body = (
                f"Your incident report ({incident.tracking_id}) was REJECTED.\n"
                f"Reason: {incident.rejection_reason or 'No specific reason provided by administrator.'}"
            )

        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[incident.contact_email],
            fail_silently=False
        )
        logger.info(f"[Approval Service] Status update sent to user {incident.contact_email} for {incident.tracking_id}")
        return True
    except Exception as e:
        logger.error(f"[Approval Service] User status dispatch failed for {incident.tracking_id}: {e}", exc_info=True)
        return False