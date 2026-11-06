import logging
from django.db import transaction
from django.utils import timezone
from ..models import IncidentSequence

logger = logging.getLogger(__name__)

def generate_incident_tracking_id(feeder_code: str, transformer_code: str) -> str:
    """
    Format: <FEEDER>/<DT>/<DDMMYY>/<SEQ_NUM>
    Example: IKJ/DT01/041126/0001
    """
    today = timezone.localdate()
    date_str = today.strftime("%d%m%y")
    clean_feeder = feeder_code.strip().upper()
    clean_dt = transformer_code.strip().upper()

    try:
        with transaction.atomic():
            # Lock the sequence row for today
            sequence_record, created = IncidentSequence.objects.select_for_update().get_or_create(
                date=today,
                defaults={'last_sequence': 0}
            )

            sequence_record.last_sequence += 1
            sequence_record.save(update_fields=['last_sequence'])

            seq_num = sequence_record.last_sequence
            tracking_id = f"{clean_feeder}/{clean_dt}/{date_str}/{seq_num:04d}"
            
            logger.info(f"[Tracking Generator] Issued tracking ID: {tracking_id}")
            return tracking_id

    except Exception as e:
        logger.error(f"[Tracking Generator] Failed to allocate atomic tracking ID: {e}", exc_info=True)
        raise RuntimeError("Unable to generate a unique tracking ID at this time.") from e