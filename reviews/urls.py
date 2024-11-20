from django.urls import path, include
from . import views

from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'reviews', views.ReviewViewSet, basename="review")

urlpatterns = [
    path('', include(router.urls)),
    ]
