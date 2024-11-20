from decimal import Decimal

from rest_framework import serializers

from django.db.models import Sum, F
from django.db import transaction
import logging


from .models import Cart, CartItem

from products.models import Product


logger = logging.getLogger(__name__)
    
  
  
class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for CartItem model.
    Handles validation and serialization of individual cart items.
    """
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source="product")
    
    class Meta:
        model = CartItem
        fields = ["id", "product_id", "quantity"]
        
    def validate_quantity(self, value):
        """
        Ensures that the quantity of a cart item is greater than zero.
        Raises a validation error if the quantity is less than or equal to zero.
        """
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
        
        
class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for the Cart model.
    Manages the creation and update of cart and cart items, and calculates the total amount.
    """
    cart_items = CartItemSerializer(many=True, required=False)
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ["id", "user", "created_at", "updated_at", "cart_items", "total_amount"]
        read_only_fields = ["user", "created_at", "updated_at"]
    
    def get_total_amount(self, obj):
        """
        Calculates the total amount of the cart by summing the price of each product
        multiplied by its quantity.
        Uses Django's `aggregate` function to optimize the database query.
        """
        total = obj.cart_items.aggregate(
            total_amount=Sum(F("quantity") * F("product__price"))
        )
        # Ensure total_amount is not None by defaulting to "0.00" if no items exist
        return total["total_amount"] or Decimal("0.00")
        
    @transaction.atomic
    def create(self, validated_data):
        """
        Creates a new cart instance along with associated cart items, if provided.
        Uses bulk creation to improve performance when creating multiple cart items.
        """
        # Extract cart items from the validated data
        cart_items_data = validated_data.pop('cart_items', None)
        # Create cart instance
        cart = Cart.objects.create(**validated_data)
        
        # If cart_items_data is provided, create the cart items in bulk
        if cart_items_data:
            cart_items = [CartItem(cart=cart, **item_data) for item_data in cart_items_data]
            CartItem.objects.bulk_create(cart_items) # Bulk create cart items for efficiency
        return cart
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Updates the cart instance and its related cart items.
        Performs bulk operations (create, update) for better performance.
        """
        # Extract cart items data
        cart_items_data = validated_data.pop("cart_items", [])
        instance.save()
        
        # Get existing cart items for the current cart
        existing_items = {item.id: item for item in instance.cart_items.all()}
        
        items_to_create = []
        items_to_update = []
        
        for item_data in cart_items_data:
            item_id = item_data.get("id", None)
            if item_id and item_id in existing_items:
                # Update existing CartItem
                item = existing_items[item_id]
                for attr, value in item_data.items():
                    setattr(item, attr, value)
                items_to_update.append(item)
            else:
                # Prepare new CartItem for bulk creation
                items_to_create.append(CartItem(cart=instance, **item_data))
        
        # Perform bulk operations for better performance
        if items_to_create:
            CartItem.objects.bulk_create(items_to_create)
        
        # Bulk update existing cart items to reduce database hits
        if items_to_update:
            CartItem.objects.bulk_update(items_to_update, fields=["product", "quantity"])
        
        return instance
