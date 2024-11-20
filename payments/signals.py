from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Transaction
from .choices import TransactionStatusChoices, OrderStatusChoices
      

@receiver(post_save, sender=Transaction)
def update_order_status(sender, instance, created, *args, **kwargs):
    if created:
        # When a Transaction is created, update the related Order's status
        order = instance.order
        if instance.status == TransactionStatusChoices.COMPLETED:
            order.status = OrderStatusChoices.PAID
        elif instance.status == TransactionStatusChoices.FAILED:
            order.status = OrderStatusChoices.FAILED
            
        order.save()
        