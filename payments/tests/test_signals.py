from django.contrib.auth import get_user_model

from django.test import TestCase
from payments.choices import TransactionStatusChoices, OrderStatusChoices
from payments.models import Transaction
from orders.models import Order


User = get_user_model()

    
class TransactionSignalTestCase(TestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            email="testuser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="F",
            role="buyer",
            phone_number="098235743",
        )
        
        # create order for user 
        self.order = Order.objects.create(
            user=self.user,
            total_amount="300.00"
        )
    
    def test_order_status_updates_on_transaction_creation(self):
        self.assertEqual(self.order.status, "pending")
        
        # Create a transaction with status 'completed'
        transaction = Transaction.objects.create(
            order=self.order,
            amount=self.order.total_amount,
            payment_method="stripe",
            status=TransactionStatusChoices.COMPLETED
        )
        
        # Fetch the updated order from the database
        self.order.refresh_from_db()
        
        # Check if the order status is updated to 'paid'
        self.assertEqual(self.order.status, OrderStatusChoices.PAID)
        
    def test_order_status_updates_on_failed_transaction(self):
        # Create a transaction with status 'failed'
        transaction = Transaction.objects.create(
            order=self.order,
            amount=self.order.total_amount,
            payment_method="stripe",
            status=TransactionStatusChoices.FAILED
        )
        # Fetch the updated order from the database
        self.order.refresh_from_db()
        
        # Check if the order status is updated to 'failed'
        self.assertEqual(self.order.status, OrderStatusChoices.FAILED)
        