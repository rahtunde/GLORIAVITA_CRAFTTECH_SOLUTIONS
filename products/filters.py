from django_filters import rest_framework as filters
from .models import Product

class ProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = filters.CharFilter(lookup_expr="iexact")
    
    class Meta:
        model = Product
        fields = ["category", "inventory", "min_price", "max_price"]