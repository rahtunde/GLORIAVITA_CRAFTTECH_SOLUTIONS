
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch

from orders.models import Order
from payments.choices import  TransactionStatusChoices
from payments.models import Transaction

User = get_user_model()


class GenerateToken:
    def __init__(self, user):
        self.user = user
        
    def generate_jwt_token(self):
        refresh = RefreshToken.for_user(self.user)
        return  str(refresh.access_token)
    
generate_token =  GenerateToken


class TransactionViewSetTestCases(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            address='123 Admin St',
            phone_number='1234567890',
            role='admin',
            password='adminpassword'
        )
        self.seller_user = User.objects.create_user(
            email="selleruser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="M",
            role="seller",
            phone_number="098235743",
        )
        self.seller_user2 = User.objects.create_user(
            email="selleruser2@gmail.com",
            password="testuser_password2",
            first_name="test1",
            last_name="test_last",
            gender="F",
            role="seller",
            phone_number="098235743",
        )
        self.regular_user = User.objects.create_user(
            email="testuser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="M",
            role="buyer",
            phone_number="098235743",
        )
        self.admin_jwt_token = generate_token(self.admin_user).generate_jwt_token()
        self.seller_jwt_token = generate_token(self.seller_user).generate_jwt_token()
        self.regular_jwt_token = generate_token(self.regular_user).generate_jwt_token()
                
        self.order = Order.objects.create(
            user=self.regular_user,
            total_amount=1000.00
        )
        
        self.order2 = Order.objects.create(
            user=self.seller_user,
            total_amount=2000.00
        )

        
        self.list_url = reverse("transaction-list")
        # self.detail_url = reverse("transaction-detail")
        self.detail_url = lambda pk: reverse("transaction-detail", args=[pk])
        
    @patch("requests.get") # Mocking the Paystack API call
    def test_successful_paystack_transaction(self, mock_get):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        # Define the fake response Paystack would return on successful payment verification
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "status": True,
            "message": "Verification successful",
            "data": {
                "status": "success",
                "amount": self.order.total_amount * 100  # Paystack returns amount in kobo (cents)
            }
        }
        
        # Data to simulate a transaction request
        data = {
            "order_id": self.order.id,
            "payment_reference": "paystack_payment_reference",
            "payment_method": "paystack"
        }
        
        # Send a POST request to create a transaction
        response = self.client.post(self.list_url, data, format="json")
        
        # Assert that the transaction was created successfully
        self.assertEqual(response.status_code, 201)
        
        # Validate the transaction data
        transaction = Transaction.objects.get(order=self.order)
        self.assertEqual(transaction.status, "completed")
        self.assertEqual(transaction.amount, self.order.total_amount)
        
    @patch("requests.get")
    def test_failed_paystack_transaction(self, mock_get):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)

        # Define the fake response Paystack would return on failed payment verification
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "status": "True",
            "message": "verification failed",
            "data": {
                "status": "failed",
                "amount": self.order.total_amount * 100
            }
        }
        
        data = {
            "order_id": self.order.id,
            "payment_reference": "invalid_payment_reference",
            "payment_method": "paystack",
        }
        
        response = self.client.post(self.list_url, data , format="json")
                
        self.assertEqual(response.status_code, 201)
        transaction = Transaction.objects.get(order=self.order)
        self.assertEqual(transaction.status, "failed")
        
    def test_staff_can_update_transaction_status(self):
        """
        Ensure that a staff user (admin) can update the transaction's status.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        transaction = Transaction.objects.create(
            order=self.order,
            amount=500,
            payment_method="paystack",
            status="pending"
        )
        
        data = {
            "status": "completed"
        }
        
        response = self.client.patch(self.detail_url(transaction.pk), data, format="json")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], TransactionStatusChoices.COMPLETED)
        
        # Fetch the transaction again and ensure the status is updated
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, TransactionStatusChoices.COMPLETED)
        
    
    def test_non_staff_cannot_update_transaction_status(self):
        """
        Ensure that a non-staff user cannot update the transaction status.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        transaction = Transaction.objects.create(
            order=self.order,
            amount=500,
            payment_method="paystack",
            status="pending"
        )
        
        data = {
            "status": "completed"
        }
        
        response = self.client.patch(self.detail_url(transaction.pk), data, format="json")

        # Ensure the user gets a 403 Forbidden response
        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Only staff members can update transaction status.")
        
    def test_staff_can_partially_update_transaction(self):
        """
        Ensure that a staff user can partially update the transaction without providing a status.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        transaction = Transaction.objects.create(
            order=self.order,
            amount=500,
            payment_method="paystack",
            status="pending"
        )
        
        data = {
            "payment_method": "bank_transfer"
        }
        
        response = self.client.patch(self.detail_url(transaction.pk), data, format="json")

        # Ensure the user gets a 200 OK response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["payment_method"], data["payment_method"])
        
        # Ensure the status was not changed
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, TransactionStatusChoices.PENDING)
