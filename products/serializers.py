import requests
from rest_framework import serializers

from django.db.models import Avg

from .models import (Brand, Category, Product, WishList)



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
        #  Calculate the average rating for approved reviews in a single query
        average = obj.reviews.filter(is_approved=True).aggregate(average_rating=Avg("rating"))
        return average["average_rating"]  


class WishlistSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    
    class Meta:
        model = WishList
        fields = "__all__"
        read_only_fields = ["user"]
        
