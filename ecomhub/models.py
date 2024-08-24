from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import  BaseUserManager, AbstractBaseUser, PermissionsMixin
from .choices import (OrderStatusChoices, TransactionStatusChoices, UserRole,
                      GenderChoice)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        
        return self.create_user(email, password, **extra_fields)
    
    
class CustomUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    email = models.EmailField(unique=True, max_length=100)
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', 
        null=True, 
        blank=True
        )
    gender = models.CharField(
        max_length=10, 
        choices=GenderChoice.choices, 
        null=True, 
        blank=True
        )
    role = models.CharField(max_length=10, choices=UserRole.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return self.email

    def is_seller(self):
        return self.groups.filter(name="Seller").exists()
  
  
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
    in_cart = models.BooleanField(default =False)
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
   

class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20, 
        choices=OrderStatusChoices.choices, 
        default=OrderStatusChoices.PENDING
        ) 
    
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    # Deletting a product item is not recommended; as users would like to see their order history
    # even when the product is no longer available, so theis should be set to on_delete=models.PROTECTED
    # Also just avoid deleting products in general (at least product that has more than 1 order) best to 
    # add a field that can make the product deactivated instead of deleted
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # set the min_value to 1, as we dont want users to order 0 item of a product
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)


class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

# It would be nice to add a signal for Transaction post, so that when the transaction is created, 
# we can auto update the Oder status accordingly
class Transaction(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="transaction")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=TransactionStatusChoices.choices)
    
    
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    
    
class WishList(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="wishlist")
    products = models.ManyToManyField(Product)
    