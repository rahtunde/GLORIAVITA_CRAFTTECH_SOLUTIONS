from django.db import models

class UserRole(models.TextChoices):
    BUYER = "buyer", "Buyer",
    SELLER = "seller", "Seller",
    ADMIN =  "admin", "Admin"


class GenderChoice(models.TextChoices):
    MALE = "M", "Male",
    FEMALE = "F", "Female",
    OTHER = "O", "Other"
    
    
class OrderStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending",
    PROCESSING = "processing", "Processing",
    SHIPPED = "shipped", "Shipped",
    DELIVERED = "delivered", "Delivered",
    CANCELED = "canceled", "Canceled",
    PAID = "paid", "Paid",
    FAILED = "failed", "Failed",
    


class TransactionStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending",
    COMPLETED = "completed", "Completed",
    FAILED = "failed", "Failed",
    REFUNDED = "refunded", "Refunded",
