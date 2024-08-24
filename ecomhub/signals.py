from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


@receiver(post_save, sender=User)
def assign_seller_group(sender, instance, created, *args, **kwargs):
    if instance.role == "seller": 
        seller_group, _ = Group.objects.get_or_create(name="Seller")
        instance.groups.add(seller_group)
    else:
        seller_group, _ = Group.objects.get_or_create(name="Seller")
        instance.groups.remove(seller_group)
        
