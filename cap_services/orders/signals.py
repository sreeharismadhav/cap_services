from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, OrderStatusHistory
from core.utils import log_activity


@receiver(post_save, sender=Order)
def order_created(sender, instance, created, **kwargs):
    if created:
        # Create initial status history
        OrderStatusHistory.objects.create(
            order=instance,
            status=instance.status,
            notes='Order placed'
        )
        
        # Log activity
        log_activity(
            user=instance.user,
            action=f'ORDER_CREATED_{instance.order_number}',
            model_name='Order',
            object_id=instance.id,
            details={'order_number': instance.order_number, 'total': str(instance.total)}
        )


@receiver(post_save, sender=OrderStatusHistory)
def order_status_changed(sender, instance, created, **kwargs):
    if created:
        # Send notification when status changes
        # You can implement WhatsApp/SMS/Email here
        pass