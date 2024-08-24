from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"users", views.UserViewSet, basename="users")
router.register(r'products', views.ProductViewSet, basename='products')
router.register(r'categories', views.CategoryViewSet, basename='categories')
router.register(r'brands', views.BrandViewSet, basename='brands')
router.register(r'carts', views.CartViewSet, basename='carts')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'reviews', views.ReviewViewSet, basename="review")
router.register(r'wishlists', views.WishlistViewSet, basename='wishlist')
router.register(r'transaction', views.TransactionViewSet, basename='transaction')


urlpatterns = [
    path('', include(router.urls)),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
