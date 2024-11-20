from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from users.choices import  UserRole


User = get_user_model()


@receiver(post_save, sender=User)
def assign_seller_group(sender, instance, created, *args, **kwargs):
    seller_group, _ = Group.objects.get_or_create(name="Seller")
    if instance.role == UserRole.SELLER: 
        instance.groups.add(seller_group)
    else:
        instance.groups.remove(seller_group)
        
