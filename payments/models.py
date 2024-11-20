from django.db import models
from .choices import TransactionStatusChoices
from orders.models import Order
   

class Transaction(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="transaction")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=TransactionStatusChoices.choices)
 