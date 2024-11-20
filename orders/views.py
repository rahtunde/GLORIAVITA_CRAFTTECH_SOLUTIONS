from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.shortcuts import get_object_or_404
from django.db import transaction

from .choices import OrderStatusChoices

from .models import Order, OrderItem
from .serializers import OrderSerializer

from products.models import Product

from drf_yasg.utils import swagger_auto_schema

               
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related("user").prefetch_related("order_items__product").order_by("id")
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Preload related objects for efficiency
            return Order.objects.all().select_related("user").prefetch_related("order_items__product").order_by("id")
        return Order.objects.filter(user=user).select_for_update("user").prefetch_related("order_items__product").order_by("id")
    
    def perform_create(self, serializer):
        """
        Override to associate the order with the current user.
        """
        serializer.save(user=self.request.user)
    
    def get_permissions(self):
        """
        Customize permissions based on the action.
        """
        if self.action in ["update", "partial_update", "destroy", "change_status"]:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    @swagger_auto_schema(
        operation_description="Add an item to the cart.",
        request_body=OrderSerializer,
        responses={200: OrderSerializer, 400: "Bad request"}
    )
    @action(detail=False, methods=["POST"])
    @transaction.atomic
    def add_to_cart(self, request):
        """
        Custom action to add items to the cart.
        """
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        
        product = get_object_or_404(Product, id=product_id)
        
        if product.inventory < quantity:
            return Response({"error": "Insufficient inventory"}, status=status.HTTP_400_BAD_REQUEST)
        
        if quantity <= 0 :
            return Response({"error": "Quantity must be positive"}, status=status.HTTP_400_BAD_REQUEST)
        
        order, created = Order.objects.get_or_create(
            user=request.user,
            status=OrderStatusChoices.PENDING
        )
        
        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            product=product,
            defaults= {"quantity": quantity, "price": product.price}
        )
        
        if not created:
            order_item.quantity +=quantity
            order_item.save()
            
        # Update total_amount and save the order
        order.total_amount = sum(item.quantity * item.price for item in order.order_items.all())
        order.save()
        
        return Response(
            {"message": f"Product '{product.name}' (ID: {product.id}) added to cart. Quantity: {quantity}"},
            status=status.HTTP_200_OK
        )
    
    @swagger_auto_schema(
        operation_description="Change order status.",
        request_body=OrderSerializer,
        responses={200: OrderSerializer, 400: "Bad request"}
    )
    @action(detail=True, methods=["POST"])
    @transaction.atomic
    def change_status(self, request, pk=None):
        """
        Custom action to change order status.
        """
        order = self.get_object()
        new_status = request.data.get("status")
            
        if new_status not in OrderStatusChoices.values:
            return Response(
                {"error": f"Invalid status. Allowed values are: {','.join(OrderStatusChoices.values)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = new_status
        order.save()
        
        return Response(
            {"message": f"Order status updated to {new_status}"},
            status=status.HTTP_200_OK
        )

