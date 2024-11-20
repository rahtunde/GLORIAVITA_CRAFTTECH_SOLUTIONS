
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.urls import reverse

from products.models import (Brand, Product, Category, WishList)

User = get_user_model()


class GenerateToken:
    def __init__(self, user):
        self.user = user
        
    def generate_jwt_token(self):
        refresh = RefreshToken.for_user(self.user)
        return  str(refresh.access_token)
    
generate_token =  GenerateToken
        
        
class TestBrandViewSetTestCases(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            address='123 Admin St',
            phone_number='1234567890',
            role='admin',
            password='adminpassword'
        )
        self.seller_user = User.objects.create_user(
            email="selleruser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="M",
            role="seller",
            phone_number="098235743",
        )
        self.regular_user = User.objects.create_user(
            email="testuser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="M",
            role="buyer",
            phone_number="098235743",
        )
        self.admin_jwt_token = generate_token(self.admin_user).generate_jwt_token()
        self.seller_jwt_token = generate_token(self.seller_user).generate_jwt_token()
        self.regular_jwt_token = generate_token(self.regular_user).generate_jwt_token()
        
        self.brand1 = Brand.objects.create(
            name="BrandX",
            description='A popular brand X'
        )
        self.brand2 = Brand.objects.create(
            name="BrandY",
            description='A popular brand Y'
        )
        self.list_url = reverse("brands-list")
        self.detail_url = reverse("brands-detail", args=[self.brand2.id])
        
    def test_admin_can_view_all_brands(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        response = self.client.get(self.list_url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], Brand.objects.count())
       
    def test_seller_can_view_all_brands(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        response = self.client.get(self.list_url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], Brand.objects.count())
     
    def test_regular_user_can_view_all_brands(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        response = self.client.get(self.list_url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], Brand.objects.count())
    
    def test_seller_can_create_brand(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        data = {"name": "BrandXY"}
        response = self.client.post(self.list_url, data, format="json")
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], data["name"])
        self.assertEqual(Brand.objects.count(), 3)
    
    def test_regular_user_cannot_create_brand(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        data = {"name": "BrandXY"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Brand.objects.count(), 2)
        
    def test_seller_can_update_brand(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        data = {
            "name": "updated BrandXXY",
            "description": "Updated brand"
        }
        response = self.client.patch(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.brand2.refresh_from_db()
        self.assertEqual(self.brand2.name, data["name"])
        
    def test_regular_user_cannot_update_brand(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        data = {
            "name": "updated BrandXXY",
            "description": "Updated brand"
        }
        response = self.client.patch(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, 403)
        
    def test_seller_can_delete_brand(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(response.data)
    
    def test_regular_user_cannot_delete_brand(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, 403)
                
        
class CategoryViewSetTestCases(APITestCase):
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            address='123 Admin St',
            phone_number='1234567890',
            role='admin',
            password='adminpassword'
        )
        self.seller_user = User.objects.create_user(
            email="selleruser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="M",
            role="seller",
            phone_number="098235743",
        )
        self.regular_user = User.objects.create_user(
            email="testuser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="M",
            role="buyer",
            phone_number="098235743",
        )
        self.admin_jwt_token = generate_token(self.admin_user).generate_jwt_token()
        self.seller_jwt_token = generate_token(self.seller_user).generate_jwt_token()
        self.regular_jwt_token = generate_token(self.regular_user).generate_jwt_token()
        
        self.category = Category.objects.create(
            name="Electronics",
            description="Best electronic"
        )
        
        self.list_url = reverse("categories-list")
        self.detail_url = reverse("categories-detail", args=[self.category.id])
        
    def test_admin_can_view_all_categories(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        
    def test_seller_can_view_all_categories(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
       
    def test_regular_user_can_view_all_categories(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        
    def test_seller_can_create_category(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        
        data = {
            "name": "Appliances",
            "description": "Home Appliances"
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], data["name"])
        self.assertEqual(Category.objects.count(), 2)
        
    def test_regular_user_cannot_create_category(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        data = {
            "name": "Appliances",
            "description": "Home Appliances"
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Category.objects.count(), 1)
        
    def test_seller_can_update_category(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        
        data = {
            "name": "Updated Electronics",
            "description": "updated Electronics description"
        }
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.category.refresh_from_db()
        self.assertEqual(response.data["name"], data["name"])
        
    def test_regular_user_cannot_update_category(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        data = {
            "name": "Updated Electronics",
            "description": "updated Electronics description"
        }
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, 403)
        
        
    def test_seller_can_delete_category(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(response.data)
    
    def test_regular_user_cannot_delete_category(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, 403)
    
        

class ProductViewSetTestCases(APITestCase):
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            address='123 Admin St',
            phone_number='1234567890',
            role='admin',
            password='adminpassword'
        )
        self.seller_user = User.objects.create_user(
            email="selleruser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="M",
            role="seller",
            phone_number="098235743",
        )
        self.seller_user2 = User.objects.create_user(
            email="selleruser2@gmail.com",
            password="testuser_password2",
            first_name="test1",
            last_name="test_last",
            gender="F",
            role="seller",
            phone_number="098235743",
        )
        self.regular_user = User.objects.create_user(
            email="testuser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="M",
            role="buyer",
            phone_number="098235743",
        )
        self.admin_jwt_token = generate_token(self.admin_user).generate_jwt_token()
        self.seller_jwt_token = generate_token(self.seller_user).generate_jwt_token()
        self.regular_jwt_token = generate_token(self.regular_user).generate_jwt_token()
        
        self.category = Category.objects.create(
            name="Electronics",
            description="Best electronic"
        )
        self.brand = Brand.objects.create(
            name="BrandX",
            description="Best Brand"
        )
        
        self.product = Product.objects.create(
            name="Laptop",
            description="A powerful laptop",
            price=1300.00,
            category=self.category,
            brand=self.brand,
            seller=self.seller_user,
            in_stock=True,
            inventory=5,
        )
        
        self.product2 = Product.objects.create(
            name="Laptop",
            description="A powerful laptop",
            price=1300.00,
            category=self.category,
            brand=self.brand,
            seller=self.seller_user2,
            in_stock=False,
            inventory=5,
        )
        
        self.list_url = reverse("products-list")
        self.detail_url = reverse("products-detail", args=[self.product.id])
        self.deactivate_product_url = reverse("products-deactivate", args=[self.product.id])
        
        
    def test_admin_can_view_all_products(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)
        
    def test_seller_can_view_their_products(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["seller"], self.seller_user.id)
        self.assertEqual(len(response.data["results"]), 1)
        
    def test_regular_user_can_view_in_stock_products(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        
    def test_seller_can_create_product(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        data = {
            'name': 'Smartphone',
            'description': 'A high-end smartphone',
            'price': 999.99,
            'category': self.category.id,
            'brand': self.brand.id,
            'in_stock': True
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["seller"], self.seller_user.id)
        self.assertEqual(Product.objects.count(), 3)
        
    def test_regular_user_cannot_create_product(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        data = {
            'name': 'Smartphone',
            'description': 'A high-end smartphone',
            'price': 999.99,
            'category': self.category.id,
            'brand': self.brand.id,
            'in_stock': True
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Product.objects.count(), 2)
        
    def test_seller_can_update_own_product(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        data = {
            'name': 'updated Laptop',
            'description': 'Updated Laptop description',
            'price': 1200.00,
        }
        response = self.client.patch(self.detail_url, data, format="json")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], data["name"])
        self.assertEqual(response.data["description"], data["description"])
        
    def test_regular_user_cannot_update_product(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        data = {
            'name': 'updated Laptop',
            'description': 'Updated Laptop description',
            'price': 1200.00,
        }
        response = self.client.patch(self.detail_url, data, format="json")
        
        self.assertEqual(response.status_code, 403)
    
    def test_seller_can_delete_own_product(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(response.data)
    
    def test_staff_can_deactivate_product(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        response = self.client.post(self.deactivate_product_url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.data["detail"], "Product deactivated")
        
    def test_seller_can_deactivate_product(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        
        response = self.client.post(self.deactivate_product_url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.data["detail"], "Product deactivated")
    
    def test_regular_cannot_deactivate_product(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        response = self.client.post(self.deactivate_product_url)
        self.assertEqual(response.status_code, 403)   



class WishListViewSetTestCases(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            address='123 Admin St',
            phone_number='1234567890',
            role='admin',
            password='adminpassword'
        )
        self.seller_user = User.objects.create_user(
            email="selleruser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="M",
            role="seller",
            phone_number="098235743",
        )
        self.seller_user2 = User.objects.create_user(
            email="selleruser2@gmail.com",
            password="testuser_password2",
            first_name="test1",
            last_name="test_last",
            gender="F",
            role="seller",
            phone_number="098235743",
        )
        self.regular_user = User.objects.create_user(
            email="testuser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="M",
            role="buyer",
            phone_number="098235743",
        )
        self.admin_jwt_token = generate_token(self.admin_user).generate_jwt_token()
        self.seller_jwt_token = generate_token(self.seller_user).generate_jwt_token()
        self.regular_jwt_token = generate_token(self.regular_user).generate_jwt_token()
        
        self.category = Category.objects.create(
            name="Electronics",
            description="Best electronic"
        )
        self.brand = Brand.objects.create(
            name="BrandX",
            description="Best Brand"
        )
        
        self.product = Product.objects.create(
            name="Laptop",
            description="A powerful laptop",
            price=1300.00,
            category=self.category,
            brand=self.brand,
            seller=self.seller_user,
            in_stock=True,
            inventory=5,
        )
        
        self.product2 = Product.objects.create(
            name="Laptop",
            description="A powerful laptop",
            price=1300.00,
            category=self.category,
            brand=self.brand,
            seller=self.seller_user2,
            in_stock=False,
            inventory=5,
        )
        
        self.wishlist = WishList.objects.create(user=self.admin_user)
        self.list_url = reverse("wishlist-list")
        self.detail_url = reverse("wishlist-detail", args=[self.wishlist.pk])
        
    def test_create_wishlist(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
               
        response = self.client.post(self.list_url, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"], self.seller_user.id)
        
    def test_add_product_to_wishlist(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        url = reverse("wishlist-add-product")
        data = {
            "product_id": self.product.id
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)        
        self.assertEqual(response.data["status"], "Product added to wishlist")
        self.assertIn(self.product, self.wishlist.products.all())
        
    def test_add_product_to_wishlist_without_product_id(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        url = reverse("wishlist-add-product")
        
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, 400)        
        self.assertEqual(response.data["error"], "Product ID is required")
        
    def test_add_product_invalid_id(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        
        url = reverse("wishlist-add-product")
        data = {
            "product_id": 10000
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 404)
        
    def test_remove_product_from_wishlist(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        url = reverse("wishlist-remove-product")
        data = {
            "product_id": self.product.id
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)        
        self.assertEqual(response.data["status"], "Product removed from wishlist")
        self.assertNotIn(self.product, self.wishlist.products.all())
    
    def test_remove_product_from_wishlist_invalid_id(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        url = reverse("wishlist-remove-product")
        data = {
            "product_id": 300
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 404)
        
    def test_remove_product_from_wishlist_without_product_id(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        url = reverse('wishlist-remove-product')
        response = self.client.post(url, {}, format='json')        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Product ID is required')
