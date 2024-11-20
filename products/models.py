from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
# from django.contrib.auth.models import  BaseUserManager, AbstractBaseUser, PermissionsMixin
from users.models import CustomUser

  
class Brand(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        permissions = [
            ("can_manage_brand", "Can manage brand"),
        ]
      
      
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        permissions = [
            ("can_manage_category", "Can manage category"),
        ]
    
    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    inventory = models.PositiveIntegerField(default=0)
    in_stock = models.BooleanField(default=True)
    in_cart = models.BooleanField(default=False)
    deactivated = models.BooleanField(default=False)
    image = models.ImageField(
        null=True,
        blank=True
    )
    
    class Meta:
        permissions = [
            ("can_manage_product", "Can manage product"),
        ]
    
    def __str__(self) -> str:
        return self.name

   
class WishList(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="wishlist")
    products = models.ManyToManyField(Product)
 