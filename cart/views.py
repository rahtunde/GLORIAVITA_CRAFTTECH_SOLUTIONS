from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Cart, CartItem
from .serializers import CartSerializer


from products.models import Product

from drf_yasg.utils import swagger_auto_schema

User = get_user_model()
                

class CartViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides operations for managing the user's shopping cart.

    Handles cart creation, item addition/removal, updating item quantities, 
    and clearing the cart. Each user can only have one cart.
    """
    queryset = Cart.objects.all().select_related("user").prefetch_related("cart_items__product").order_by("id")
    serializer_class = CartSerializer
    
    def get_queryset(self):
        """
        Retrieve the cart based on the user's role:
        - If the user is staff, retrieve all carts.
        - Otherwise, return only the carts belonging to the current user.
        """
        user = self.request.user
        if user.is_staff:
            # Efficiently preload related objects for admin users
            return Cart.objects.all().select_related("user").prefetch_related("cart_items__product").order_by("id")
        return Cart.objects.filter(user=user).select_related("user").prefetch_related("cart_items__product").order_by("id")
    
    def perform_create(self, serializer):
        """
        Set the cart's owner to the currently authenticated user when creating a new cart.
        """
        serializer.save(user=self.request.user)
        
    def create(self, request, *args, **kwargs):
        """
        Create a new cart for the user. If the user already has a cart, return an error response.
        Only one cart is allowed per user.
        """
        
        # Check if user already has a cart
        if Cart.objects.filter(user=request.user).exists():
            return Response({"detail": "User already has a cart"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a new cart if it doesn't exist
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="Add an item to the cart.",
        request_body=CartSerializer,
        responses={200: CartSerializer, 400: "Bad request"}
    )
    @action(detail=True, methods=["POST"])
    def add_item(self, request, pk=None):
        """
        Add a product to the cart. If the product already exists in the cart, increment the quantity.
        - Validates that the product exists and ensures a positive quantity.
        """
        cart = self.get_object() # Get the cart instance 
        product_id = request.data.get("product")
        quantity = int(request.data.get("quantity", 1))
        
        # Retrieve the product and validate existence
        product = get_object_or_404(Product, id=product_id)
        
        # Ensure quantity is positive
        if quantity <= 0:
            return Response({"detail": "Quantity must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the cart already contains the product
        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)
            # If it exists, update the quantity
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            # If it does not exist, create a new cart item
            CartItem.objects.create(cart=cart, product=product, quantity=quantity)

        # Refresh the cart instance to reflect the changes
        cart.refresh_from_db()
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Allow user to remove item from cart.",
        request_body=CartSerializer,
        responses={200: CartSerializer, 400: "Bad request"}
    )
    @action(detail=True, methods=["POST"])
    def remove_item(self, request, pk=None):
        """
        Remove a product from the cart based on the provided product ID.
        - Validates that the product exists in the cart.
        """
        cart = self.get_object()
        product_id = request.data.get("product")
        
        # Retrieve the cart item and delete it
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        cart_item.delete()
        
        # Refresh the cart instance to reflect the changes
        cart.refresh_from_db()
        
        # Return updated cart data
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Allow user to update cart item.",
        request_body=CartSerializer,
        responses={201: CartSerializer, 400: "Bad request"}
    )  
    @action(detail=True, methods=["put"])
    def update_item(self, request, pk=None):
        """
        Update the quantity of a product in the cart.
        - Validates the product ID and quantity before updating the item.
        """
        cart = self.get_object()
        cart_item_data = {
            "product_id": request.data.get("product_id"),
            "quantity": int(request.data.get("quantity", 1))        
        }
        # Validate and update the cart item through the serializer
        serializer = self.get_serializer(cart, data={"cart_items": [cart_item_data]}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return updated cart data
        return Response(serializer.data)    
    
    @swagger_auto_schema(
        operation_description="Clear cart items.",
        request_body=CartSerializer,
        responses={204: CartSerializer, 400: "Bad request"}
    )
    @action(detail=True, methods=["POST"])
    def clear(self, request, pk=None):
        """
        Clear all items from the cart.
        - If the cart is already empty, return an error response.
        """
        cart = self.get_object()
        
        if not cart.cart_items.exists():
            return Response("The cart is already empty.", status=status.HTTP_400_BAD_REQUEST)
        
        # Bulk delete all items
        cart.cart_items.all().delete()
        
        serializer = self.get_serializer(cart)
        # return the empty cart
        return Response(serializer.data)
