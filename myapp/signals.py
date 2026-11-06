import logging
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .cache_keys import CACHE_KEY_DASHBOARD
from .models import Feeder, OrderItem, Order

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Feeder)
@receiver(post_delete, sender=Feeder)
def invalidate_feeder_dashboard_cache(sender, using, **kwargs):
    def invalidate():
        try:
            cache.delete(CACHE_KEY_DASHBOARD)
        except Exception:
            logger.warning("Could not invalidate feeder dashboard cache", exc_info=True)

    transaction.on_commit(invalidate, using=using)


@receiver(post_save, sender=OrderItem)
def update_order_status_on_item_completion(sender, instance, created, raw, **kwargs):
    if raw:
        return
    """
    Automatically updates the parent Order status to 'ready_for_dispatch'
    if all associated items are marked as 'completed'.
    """
    order = instance.order
    items = order.items.all()
    
    if not items.exists():
        return

    all_completed = items.filter(status='completed').count() == items.count()
    
    if all_completed and order.status != 'ready_for_dispatch':
        order.status = 'ready_for_dispatch'
        order.save()
        logger.info(f"Order {order.id} status updated to 'ready_for_dispatch' because all items are completed.")
