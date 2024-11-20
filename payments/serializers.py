import requests
from rest_framework import serializers

from django.conf import settings
import logging

from .choices import OrderStatusChoices, TransactionStatusChoices
from orders.serializers import OrderSerializer

from .models import Transaction
from orders.models import Order


logger = logging.getLogger(__name__)


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for handling transactions, including order validation,
    payment processing via Paystack, and transaction creation.
    """
    order = OrderSerializer(read_only=True)
    payment_reference = serializers.CharField(write_only=True) # For Paystack payment reference 
    status = serializers.ChoiceField(choices=TransactionStatusChoices.choices, default="pending")

    
    class Meta:
        model = Transaction
        fields = ["id", "order", "amount", "transaction_date", "payment_method", "status", "payment_reference"]
        read_only_fields = ["transaction_date", "amount"]
        
    def __init__(self, *args, **kwargs):
        """
        Override to set the 'status' field to read-only unless the user is a staff member
        and the request is an update.
        """
        super().__init__(*args, **kwargs)
        
        # Access the request context
        request = self.context.get("request")
        
        # If the user is not staff, or the request is not a PATCH/PUT, make the status read-only
        if request and not request.user.is_staff:
            self.fields["status"].read_only = True
        elif request and request.method in ["POST", "GET"]:  # During creation or retrieval, make it read-only
            self.fields["status"].read_only = True
        
    
    def create(self, validated_data):
        """
        Create a transaction by processing the payment through Paystack.
        Ensures valid order ID, processes the payment, and updates the transaction and order status.
        """
        order_id = self.context["request"].data.get("order_id")
        if not order_id:
            raise serializers.ValidationError("Order ID is required.")

        # Fetch the payment method and payment reference
        payment_method = validated_data.pop("payment_method")
        payment_reference = validated_data.pop("payment_reference")
        
        # Supported payment method list
        payment_method_list = ["paystack", "bank_transfer"]
        if payment_method not in payment_method_list:
            raise serializers.ValidationError({"error": "Invalid payment method."})
        
        # Validate and fetch the order
        order = self.get_order(order_id)
        
        # Process payment via Paystack
        payment_status = self.process_paystack_payment(order, payment_reference)
        
        # Create the transaction record with the appropriate status
        status = TransactionStatusChoices.COMPLETED if payment_status == "success" else TransactionStatusChoices.FAILED  
        transaction = self.create_transaction(order, payment_method, status, validated_data)
        
        # Update the order status based on the payment result
        order.status = OrderStatusChoices.PAID if status == TransactionStatusChoices.COMPLETED else OrderStatusChoices.FAILED
        # order.status = OrderStatusChoices.PAID if payment_status == "success" else OrderStatusChoices.FAILED
        order.save()
        
        return  transaction
    
    def process_paystack_payment(self, order, payment_reference):
        """
        Processes the payment with Paystack by verifying the payment reference.
        """
        try:
            url = f"https://api.paystack.co/transaction/verify/{payment_reference}"
            headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
            response = requests.get(url, headers=headers)
            result = response.json()
            
            if result["status"] and result["data"]["status"] == "success":
                return "success"
            else:
                return "failed"
        
        except requests.RequestException as e:
            logger.error(f"Error verifying payment: {e}")
            return "failed"
    
    def create_transaction(self, order, payment_method, status, validated_data):
        """
        Creates the transaction record in the database.
        """
        
        return Transaction.objects.create(
            order=order,
            amount=order.total_amount,
            payment_method=payment_method,
            status=status,
            ** validated_data
        )
        
    def get_order(self, order_id):
        """
        Helper method to retrieve the order by ID. Raises an error if the order does not exist.
        """
        try:
            return Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")
        
    # def update(self, instance, validated_data):
    #     if "status" in validated_data:
    #         instance.status = validated_data.pop("status")
            
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)
        
    #     instance.save()
    #     return instance    