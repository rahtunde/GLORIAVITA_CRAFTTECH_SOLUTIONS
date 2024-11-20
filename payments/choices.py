from django.db import models    

    
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
