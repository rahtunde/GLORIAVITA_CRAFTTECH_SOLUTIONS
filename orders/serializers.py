
from rest_framework import serializers

from django.db.models import Sum, F
from django.db import transaction
import logging

from .choices import OrderStatusChoices

from .models import Order, OrderItem
from products.models import Product


logger = logging.getLogger(__name__)
    

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
        
    class Meta:
        model = Order
        fields = ["id", "user", "status", "order_items","total_amount", "created_at", "updated_at"]
        read_only_fields = ["user", "created_at", "updated_at"]
    
    def get_total_amount(self, obj):
        # Calculate the total amount using the aggregate function
        # total = obj.order_items.aggregate(
        #     total_amount=Sum(F("quantity") * F("price"))
        # )
        # return total["total_amount"]
        return obj.total_amount
        
    def validate_order_items(self, order_items):
        # Fetch all product IDs at once to minimize database queries
        product_ids = [item["product"].id for item in order_items]
        products = Product.objects.filter(id__in=product_ids)
        
        # Create a map of product_id to product for validation
        product_map = {product.id: product for product in products}
        
        for item in order_items:
            product = product_map.get(item["product"].id)
            quantity = item["quantity"]
            
            if not product:
                raise serializers.ValidationError(f"Product with id {item[product.id]} does not exist.")
            if product.inventory < quantity:
                raise serializers.ValidationError(f"Insufficient inventory for product {product.id}")
            return order_items
 
    @transaction.atomic
    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items')
        order = Order.objects.create(**validated_data)
        
        # Bulk create OrderItems efficiently
        order_items = [
            OrderItem(order=order, **item_data) for item_data in order_items_data
            ]
        OrderItem.objects.bulk_create(order_items)
        
        # Calculate total_amount and update the order (aggregate in DB)
        total_amount = OrderItem.objects.filter(order=order).aggregate(
            total=Sum(F("quantity") * F("price"))
        )["total"]
        order.total_amount = total_amount
        order.save()
        return order
        
    @transaction.atomic
    def update(self, instance, validated_data):
        order_items_data = validated_data.pop('order_items', [])
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        
        # Handle existing items and new items
        existing_items = {item.id: item for item in instance.order_items.all()}
        
        items_to_create = []
        items_to_update = []
        
        # Update or create items
        for order_item_data in order_items_data:
            item_id = order_item_data.get('id', None)
            if item_id and item_id in existing_items:
                item = existing_items[item_id]
                for attr, value in order_item_data.items():
                    setattr(item, attr, value) 
                items_to_update.append(item) 
            else:
                items_to_create.append(OrderItem(order=instance, **order_item_data))
        
        # Bulk create and update
        OrderItem.objects.bulk_create(items_to_create)
        if items_to_update:
            OrderItem.objects.bulk_update(items_to_update, ["product", "quantity", "price"])
                
    
        # Remove items not present in the update data
        items_to_keep = {item_data.get("id") for item_data in order_item_data if "id" in item_data}
        items_to_delete = [item_id for item_id in existing_items if item_id not in items_to_keep]
        
        if items_to_delete:
            OrderItem.objects.filter(id__in=items_to_delete).delete()
            
        return instance
