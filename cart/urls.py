from django.urls import path, include
from . import views

from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'carts', views.CartViewSet, basename='carts')

urlpatterns = [
    path('', include(router.urls)),
    ]
