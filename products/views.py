from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import (Product, Brand, Category, WishList
                     )
from .serializers import (ProductSerializer, CategorySerializer,
                          BrandSerializer, WishlistSerializer)

from .filters import ProductFilter
from .permissions import (IsSellerOrReadOnly, IsSellerOrStaffOrReadOnly)
from products.models import Product

from drf_yasg.utils import swagger_auto_schema


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by("id")
    serializer_class = BrandSerializer
    permission_classes = [IsSellerOrReadOnly]
    
    
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsSellerOrReadOnly]
       

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(deactivated=False).select_related("brand", "category", "seller").order_by("id") # return only active product
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
            return Product.objects.all().select_related("brand", "category", "seller").order_by("id")
        elif self.request.user.groups.filter(name="Seller").select_related("brand", "category", "seller").exists():
            return Product.objects.filter(seller=self.request.user).order_by("id")
        return Product.objects.filter(in_stock=True).select_related("brand", "category", "seller").order_by("id")
    
    @swagger_auto_schema(
        operation_description="Allow seller or staff to deactivate a product when it's not available.",
        request_body=ProductSerializer,
        responses={200: ProductSerializer, 400: "Bad request"}
    )
    @action(detail=True, methods=["POST"], permission_classes=[IsSellerOrStaffOrReadOnly])
    def deactivate(self, request, pk=None):
        product = self.get_object()
        product.deactivated = True
        product.save()
        return Response({"detail": "Product deactivated"}, status=status.HTTP_200_OK)
                
class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return WishList.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Add product to wishlist.",
        request_body=WishlistSerializer,
        responses={200: WishlistSerializer, 400: "Bad request"}
    )   
    @action(detail=False, methods=["post"])
    def add_product(self, request):
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        wishlist, created = WishList.objects.get_or_create(user=request.user)
        product = get_object_or_404(Product, id=product_id)
        wishlist.products.add(product)
        return Response({"status": "Product added to wishlist"}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Remove product from wishlist.",
        request_body=WishlistSerializer,
        responses={200: WishlistSerializer, 400: "Bad request"}
    )
    @action(detail=False, methods=["post"])
    def remove_product(self, request):
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        wishlist = get_object_or_404(WishList, user=request.user)
        product = get_object_or_404(Product, id=product_id)
        wishlist.products.remove(product)
        return Response({"status": "Product removed from wishlist"}, status=status.HTTP_200_OK)
    
