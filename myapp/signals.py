import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OrderItem, Order

logger = logging.getLogger(__name__)

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
