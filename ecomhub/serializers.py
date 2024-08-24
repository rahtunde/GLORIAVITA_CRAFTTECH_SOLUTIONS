from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
import stripe.error
import logging

from ecomhub.choices import OrderStatusChoices, TransactionStatusChoices

from .models import (Brand, Category, Product, Order, 
                     OrderItem, Transaction, Cart,
                     CartItem, Review, WishList)

import stripe

User = get_user_model()
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {
            'password': {'write_only': True}
        }
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data.get('password'))
        return  super(UserSerializer, self).create(validated_data)
    
    def update(self, instance, validated_data):
        if "password" in validated_data:
            validated_data["password"] = make_password(validated_data.get('password'))
        return super(UserSerializer, self).update(instance, validated_data)
    

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            "user_id": self.user.id
        })
        return data


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try: 
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value
    
    def save(self, **kwargs):
        email = self.validated_data["email"]
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        reset_link = f"https://localhost:8000/reset-password/{uid}/{token}/"
        
        send_mail(
            'Password Reset',
            f'Click the following link to reset your password: {reset_link}',
            'noreply@localhost.com',
            [email],
            fail_silently=False,
        )
    

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = "__all__"
        
        
class CategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    average_rating = serializers.SerializerMethodField()
        
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["seller"]
        
    def get_average_rating(self, obj):
        approved_reviews = obj.reviews.filter(is_approved=True)
        if approved_reviews.exists():
            return sum(review.rating for review in approved_reviews) / approved_reviews.count()
        return None
               

class OrderItemSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "price"]
        
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
        

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True)
    # total = serializers.SerializerMethodField()
        
    class Meta:
        model = Order
        fields = ["id", "user", "status", "order_items","total_amount", "created_at", "updated_at"]
        read_only_fields = ["user", "created_at", "updated_at"]
    
    def get_total_amount(self, obj):
        return sum(item.quantity * item.price for item in obj.order_items.all())
    
    def validate_order_items(self, order_items):
        for item in order_items:
            product = item["product"]
            quantity = item["quantity"]
            
            if not Product.objects.filter(id=product.id).exists():
                raise serializers.ValidationError(f"Product with id {product.id} does not exist.")
            if product.inventory < quantity:
                raise serializers.ValidationError(f"Insufficient inventory for product {product.id}")
            return order_items
 
    @transaction.atomic
    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items')
        order = Order.objects.create(**validated_data)
        
        order_items = [OrderItem(order=order, **item_data) for item_data in order_items_data]
        OrderItem.objects.bulk_create(order_items)
        
        # Calculate total_amount and update the order
        order.total_amount = sum(item.quantity * item.price for item in order.order_items.all())
        return order
        
    @transaction.atomic
    def update(self, instance, validated_data):
        order_items_data = validated_data.pop('order_items', [])
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        
        # Update or create order items
        existing_items = {item.id: item for item in instance.order_items.all()}
        
        items_to_create = []
        items_to_update = []
        
        for order_item_data in order_items_data:
            item_id = order_item_data.get('id', None)
            if item_id and item_id in existing_items:
                item = existing_items[item_id]
                for attr, value in order_item_data.items():
                    setattr(item, attr, value) 
                items_to_update.append(item) 
            else:
                items_to_create.append(OrderItem(order=instance, **order_item_data))
        
        OrderItem.objects.bulk_create(items_to_create)
        OrderItem.objects.bulk_update(items_to_update, ["product", "quantity", "price"])
                
    
        # Remove items not present in the update data
        items_to_keep = {item_data.get("id") for item_data in order_item_data if "id" in item_data}
        items_to_delete = [item_id for item_id in existing_items if item_id not in items_to_keep]
        
        if items_to_delete:
            OrderItem.objects.filter(id__in=[item.id for item in items_to_delete]).delete()
            
        return instance
  
  
class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source="product")
    # product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CartItem
        fields = ["id", "product_id", "quantity"]
        
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
        
        
class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, required=False)
    total = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ["id", "user", "created_at", "updated_at", "cart_items", "total"]
        read_only_fields = ["user", "created_at", "updated_at"]
    
    def get_total(self, obj):
        return sum(item.product.price * item.quantity for item in obj.cart_items.all())    
    
    @transaction.atomic
    def create(self, validated_data):
        cart_items_data = validated_data.pop('cart_items', None)
        cart = Cart.objects.create(**validated_data)
        if cart_items_data:
            for cart_item_data in cart_items_data:
                CartItem.objects.create(cart=cart, **cart_item_data)
        return cart
    
    @transaction.atomic
    def update(self, instance, validated_data):
        cart_items_data = validated_data.pop('cart_items')
        instance.save()
        
        # Update or create cart items
        for cart_item_data in cart_items_data:
            cart_item_id = cart_item_data.get('id', None)
            if cart_item_id:
                item = CartItem.objects.get(id=cart_item_id, cart=instance)
                item.product = cart_item_data.get('product', item.product)
                item.quantity = cart_item_data.get('quantity', item.quantity)
                item.save()
            else:
                CartItem.objects.create(cart=instance, **cart_item_data)
        
        return instance
  
    
class TransactionSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    stripe_token = serializers.CharField(write_only=True)
    status = serializers.ChoiceField(choices=TransactionStatusChoices.choices, read_only=True)
    
    class Meta:
        model = Transaction
        fields = ["id", "order", "amount", "transaction_date", "payment_method", "status", "stripe_token"]
        read_only_fields = ["transaction_date", "amount"]
        
    def create(self, validated_data):
        order_id = self.context["request"].data.get("order_id")
        payment_method = validated_data.pop("payment_method")
        stripe_token = validated_data.pop("stripe_token")
        payment_method_list = ["stripe"]
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")
        
        if payment_method not in payment_method_list:
            raise serializers.ValidationError({"error": "invalid payment method."})
        # Process the payment with stripe
        try:
            charge = stripe.Charge.create(
                amount=int(order.total_amount * 100), # stripe expect amount in cents
                currency="usd",
                source=stripe_token,
                description=f"Charge for order{order.id}"
            )
            # Create transaction
            transaction = Transaction.objects.create(
                order=order,
                amount=order.total_amount,
                payment_method=payment_method,
                status= TransactionStatusChoices.COMPLETED if charge["paid"] else TransactionStatusChoices.FAILED,
                **validated_data
            )

            # Update order status
            order.status = OrderStatusChoices.PAID if charge["paid"] else OrderStatusChoices.FAILED
            order.save()
            return transaction
        
        except stripe.error.StripeError as e:
            # log error message for better debugging 
            logger.error({f"Strip error occur: {str(e)}"})
            
             # Send email to admin
            self.send_error_email("Stripe error", str(e))
            
             # Raise a ValidationError
            raise serializers.ValidationError({"detail":"An error occurred while processing your payment. Please try again later."})

        except stripe.error.RateLimitError as e:
            # If many request is made to the API quickly
            raise serializers.ValidationError("Rate limit error")
        
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            raise serializers.ValidationError("Invalid parameters")
        
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            raise serializers.ValidationError("Authentication with payment provider failed")
        
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            raise serializers.ValidationError("Network communication failed")
        
        except stripe.error.StripeError as e:
            logger.error({f"Strip error occur: {str(e)}"})
            # Send email to admin
            self.send_error_email("Stripe error", str(e))
            raise serializers.ValidationError("An error occurred while processing your payment. Please try again later.")
          
        except Exception as e:
            # Log the error
            logger.error(f"Unexpected error occurred: {str(e)}")
            
            # Send email to admin
            self.send_error_email("Unexpected error", str(e))
            
            # Generic message to user
            raise serializers.ValidationError("A system error occurred. Our team has been notified and we'll look into it.")

    def update(self, instance, validated_data):
        if "status" in validated_data:
            instance.status = validated_data.pop("status")
            
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
    
    def send_error_email(self, error_type, error_details):
        subject = f"E-commerce Error: {error_type}"
        message = f"An error occurred while processing a transaction:\n\n{error_details}"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [settings.ADMIN_EMAIL]  
        
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)


class ReviewSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ["is_approved", "user"]
        

class WishlistSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    
    class Meta:
        model = WishList
        fields = "__all__"
        read_only_fields = ["user"]
        