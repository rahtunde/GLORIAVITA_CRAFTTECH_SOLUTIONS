from rest_framework import viewsets, permissions, generics, filters, status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db import transaction

from ecomhub.choices import OrderStatusChoices, TransactionStatusChoices, UserRole

from .models import (Brand, Product, Order, OrderItem, CustomUser,
                     Cart, CartItem, Category, Review, 
                     Transaction, WishList
                     )
from .serializers import (BrandSerializer, UserSerializer, ProductSerializer, CategorySerializer,
                          CartSerializer, WishlistSerializer, OrderSerializer,
                          PasswordResetSerializer, TransactionSerializer, CustomTokenObtainPairSerializer,
                          ReviewSerializer)

from .filters import ProductFilter
from .permissions import (IsStaffOrReadOnly, IsSellerOrReadOnly, IsSellerOrStaffOrReadOnly, )
import stripe

User = get_user_model()

  
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'list']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
    
    @action(detail=False, methods=['POST'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(serializer.data,  status=201)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=["POST"], permission_classes=[permissions.AllowAny])
    def password_reset(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password reset e-mail has been sent."}, status=200)   
    
    @action(detail=True, methods=["PATCH"], permission_classes=[permissions.IsAdminUser]) 
    def update_role(self, request, pk=None):
        user = self.get_object()
        role = request.data.get("role")
        roles = ["buyer", "seller", "admin"]
        if role not in roles:
            return Response({"detail": "Invalid role."}, status=400)
        
        user.role = role
        user.save()
        return Response({"detail": f"Role updated to {role}"}, status=200)
        
        
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    create a custom class for the  token (login) to include email with its response 
    """
    serializer_class = CustomTokenObtainPairSerializer 


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by("id")
    serializer_class = BrandSerializer
    permission_classes = [IsSellerOrReadOnly]
    
    
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsSellerOrReadOnly]
       

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("id")
    serializer_class = ProductSerializer
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at"]
    permission_classes = [IsSellerOrStaffOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
        
    def get_queryset(self):
        if self.request.user.is_staff:
            return Product.objects.all().order_by("id")
        elif self.request.user.groups.filter(name="Seller").exists():
            return Product.objects.filter(seller=self.request.user).order_by("id")
        return Product.objects.filter(in_stock=True).order_by("id")
                
        
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("id")
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().order_by("id")
        return Order.objects.filter(user=user).order_by("id")
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy", "change_status"]:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=["POST"])
    @transaction.atomic
    def add_to_cart(self, request):
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        
        product = get_object_or_404(Product, id=product_id)
        
        if product.inventory < quantity:
            return Response({"error": "Insufficient inventory"}, status=status.HTTP_400_BAD_REQUEST)
        
        if quantity == 0 or quantity < 0:
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
            
        order.total_amount = sum(item.quantity * item.price for item in order.order_items.all())
        order.save()
        
        return Response(
            {"message": f"Product '{product.name}' (ID: {product.id}) added to cart. Quantity: {quantity}"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=["POST"])
    @transaction.atomic
    def change_status(self, request, pk=None):
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


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all().order_by("id")
    serializer_class = CartSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Cart.objects.all().order_by("id")
        return Cart.objects.filter(user=user).order_by("id")
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    def create(self, request, *args, **kwargs):
        # Check if user already has a cart
        existing_cart = Cart.objects.filter(user=request.user).first()
        if existing_cart:
            return Response({"detail": "User already has a cart"}, status=status.HTTP_400_BAD_REQUEST)
        
        # If not, create a new cart
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["POST"])
    def add_item(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get("product")
        quantity = int(request.data.get("quantity", 1))
        
        product = get_object_or_404(Product, id=product_id)
        
         # Ensure quantity is provided and greater than zero
        if quantity <= 0:
            return Response({"detail": "Quantity must be a positive integer."}, status=400)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity})
        
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
            
        cart_item.save()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=True, methods=["POST"])
    def remove_item(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get("product")
        
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        cart_item.delete()
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
        
    @action(detail=True, methods=["put"])
    def update_item(self, request, pk=None):
        cart = self.get_object()
        cart_item_data = {
            "product_id": request.data.get("product_id"),
            "quantity": int(request.data.get("quantity", 1))        
        }
        serializer = self.get_serializer(cart, data={"cart_items": [cart_item_data]}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)    
    
    @action(detail=True, methods=["POST"])
    def clear(self, request, pk=None):
        cart = self.get_object()
        cart_items = cart.cart_items
        
        if cart_items.count() == 0:
            return Response("The cart is already empty.", status=status.HTTP_400_BAD_REQUEST)
        
        cart.cart_items.all().delete()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(is_approved=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy", "approve", "reject"]:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
        
    @action(detail=True, methods=["POST"], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        try:
            review = self.get_object()
            if review.is_approved:
                return Response({"status": "Review is already approved."}, status=status.HTTP_400_BAD_REQUEST)
            review.is_approved = True
            review.save()
            return Response({'status': "Review approved"}, status=status.HTTP_200_OK)
        except Exception as e:
            raise ValidationError(str(e))
    
    @action(detail=True, methods=["POST"], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        review = self.get_object()
        review.delete()
        return Response({"status": "Review rejected"}, status=204)
    
    
class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return WishList.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    @action(detail=False, methods=["post"])
    def add_product(self, request):
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        wishlist, created = WishList.objects.get_or_create(user=request.user)
        product = get_object_or_404(Product, id=product_id)
        wishlist.products.add(product)
        return Response({"status": "Product added to wishlist"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["post"])
    def remove_product(self, request):
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        wishlist = get_object_or_404(WishList, user=request.user)
        product = get_object_or_404(Product, id=product_id)
        wishlist.products.remove(product)
        return Response({"status": "Product removed from wishlist"}, status=status.HTTP_200_OK)
    

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all().order_by("-transaction_date")
    serializer_class = TransactionSerializer
    # permission_classes = [IsStaffOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user 
        if user.is_staff:
            return Transaction.objects.all().order_by("-transaction_date")
        return Transaction.objects.filter(order__user=user)
     
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check if the user is staff before allowing status update
        if 'status' in request.data and not request.user.is_staff:
            return Response({"error": "Only staff members can update transaction status."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Update order status if transaction status changes
        if 'status' in serializer.validated_data:
            new_status = serializer.validated_data['status']
            order = instance.order
            if new_status == TransactionStatusChoices.COMPLETED:
                order.status = OrderStatusChoices.PAID
            elif new_status == TransactionStatusChoices.FAILED:
                order.status = OrderStatusChoices.FAILED
            order.save()

        return Response(serializer.data)