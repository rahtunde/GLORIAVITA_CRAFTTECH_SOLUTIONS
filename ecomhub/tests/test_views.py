from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.contrib.auth.models import Group
from unittest.mock import patch

import stripe
import stripe.error

from ecomhub.choices import OrderStatusChoices
from ecomhub.models import (Brand, Product, Category, Cart, CartItem,
                            Order, OrderItem, Review, WishList, 
                            Transaction)

User = get_user_model()


class GenerateToken:
    def __init__(self, user):
        self.user = user
        
    def generate_jwt_token(self):
        refresh = RefreshToken.for_user(self.user)
        return  str(refresh.access_token)
    
generate_token =  GenerateToken


class TestUserViewSetEndpoints(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="M",
            role="buyer",
            phone_number="098235743",
        )
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            address='123 Admin St',
            phone_number='1234567890',
            role='admin',
            password='adminpassword'
        )
        
        self.jwt_token = generate_token(self.admin_user).generate_jwt_token()
        self.jwt_token1 = generate_token(self.user).generate_jwt_token()
        
    def test_register_user(self):
        url = reverse("users-register")
        data = {
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'address': '123 Test St',
            'phone_number': '1234567890',
            'role': 'buyer',
            'password': 'password123'
        }
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["first_name"], data["first_name"])
        self.assertEqual(response.data["role"], data["role"])
        self.assertTrue(User.objects.filter(email=data["email"]).exists())
        
    def test_reset_password(self):
        url = reverse("users-password-reset")
        
        data = {
            "email": self.user.email
        }
        
        response = self.client.post(url, data, format="json")
        sent_mail = mail.outbox
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"], "Password reset e-mail has been sent.")
        self.assertEqual(len(sent_mail), 1)
        self.assertEqual(sent_mail[0].subject, "Password Reset")

    def test_update_user_role(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.jwt_token)
        url = reverse("users-update-role", args=[self.user.id])
        data = {
             "role": "seller"
         }
        response = self.client.patch(url , data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"], "Role updated to seller")
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, data["role"])
        
    def test_unauthorize_update_user_role(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.jwt_token1)
        url = reverse("users-update-role", args=[self.user.id])
        data = {
             "role": "seller"
         }
        response = self.client.patch(url , data, format="json")
        self.assertEqual(response.status_code, 403)
        

class TestCustomTokenObtainPairView(APITestCase):
    def test_user_login_success(self):
        user = User.objects.create_user(
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            address='123 Test St',
            phone_number='1234567890',
            role='buyer',
            password='password123'
        )
        url = reverse("login")
        data = {"email": "testuser@example.com", "password": "password123"}
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user_id"], user.id)
        
    def test_user_login_failure(self):
        url = reverse("login")
        data = {"email": "testuser@example.com", "password": "pass23"}
        
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 401)
        
        
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
        

class CartViewSetTestCases(APITestCase):
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
        
        self.cart = Cart.objects.create(
            user=self.admin_user, 
            )
        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=5)
        
        self.list_url = reverse("carts-list")
        self.detail_url = reverse("carts-detail", args=[self.cart.id])
        self.add_item_url = lambda pk: reverse("carts-add-item", args=[pk])
        self.remove_item_url = lambda pk: reverse("carts-remove-item", args=[pk])
        self.update_item_url = lambda pk: reverse("carts-update-item", args=[pk])
        self.clear_url = lambda pk: reverse("carts-clear", args=[pk])
        
    def test_regular_user_can_create_cart(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        data = {
            "cart_items": [
                {
                "product_id": self.product.id,
                 "quantity": 5
                 }
            ]
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"], self.regular_user.id)
        self.assertEqual(response.data["cart_items"][0]["quantity"], data["cart_items"][0]["quantity"])
    
    def test_create_cart_already_exists(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)

        Cart.objects.create(user=self.regular_user)
        
        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "User already has a cart")
         
    def test_regular_user_can_get_only_owned_cart(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        Cart.objects.create(user=self.regular_user)
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_add_item_to_cart(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        cart_response = self.client.post(self.list_url, {}, format="json")
        cart_id = cart_response.data["id"]
                
        data = {
            "product": self.product.id,
            "quantity": 10      
            }
        response = self.client.post(self.add_item_url(cart_id), data, format="json") 
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cart_items"][0]["product_id"], data["product"])
        self.assertEqual(len(response.data["cart_items"]), 1)
        
    def test_remove_item_from_cart(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        cart_response = self.client.post(self.list_url, {"cart_items": [{"product_id": self.product.id, "quantity":5}]}, format="json")
        cart_id = cart_response.data["id"]
        
        response = self.client.post(self.remove_item_url(cart_id), {"product": self.product.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["cart_items"]), 0)
          
    def test_update_cart_item(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        update_url = reverse("carts-update-item", args=[self.cart.id])
        data = {
            "product_id": self.product.id,
            "quantity": 5
        }
        
        response = self.client.put(update_url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.cart.refresh_from_db()
        self.assertEqual(response.data["cart_items"][0]["quantity"], data["quantity"])
 
    def test_clear_cart(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        cart_response = self.client.post(self.list_url, {"cart_items": [{"product_id": self.product2.id, "quantity":6}]}, format="json")
        cart_id = cart_response.data["id"]
        
        response = self.client.post(self.clear_url(cart_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["cart_items"]), 0)

    
class OrderViewSetTestCases(APITestCase):
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
        
        self.order = Order.objects.create(
            user=self.admin_user,
            )
        self.order2 = Order.objects.create(
            user=self.regular_user,
            )
        
        self.list_url = reverse("order-list")
        self.detail_url = reverse("order-detail", args=[self.order2.pk])
        
    def test_add_to_cart(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        url = reverse("order-add-to-cart")
        data = {
            "product_id": self.product.id,
            "quantity": 4
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"Product '{self.product.name}' (ID: 1) added to cart", response.data["message"])

        # Check if the order was created
        order_item = OrderItem.objects.get(order__user=self.regular_user, product=self.product.id)
        self.assertEqual(order_item.quantity, data["quantity"])
        
    def test_add_to_cart_insufficient_inventory(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        url = reverse("order-add-to-cart")
        data = {
            "product_id": self.product.id,
            "quantity": 100
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Insufficient inventory", response.data["error"])
        
    def test_add_to_cart_invalid_quantity(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        url = reverse("order-add-to-cart")
        data = {
            "product_id": self.product.id,
            "quantity": -1 # Invalid quantity
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Quantity must be positive", response.data["error"])
        
    def test_change_status(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        url = reverse("order-change-status", args=[self.order.pk])
        data = {
            "status": OrderStatusChoices.PROCESSING
        }
        response = self.client.post(url, data, format="json")
    
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], f"Order status updated to {OrderStatusChoices.PROCESSING}")
        
        # Check if the order status was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatusChoices.PROCESSING)
    
    def test_change_status_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        url = reverse("order-change-status", args=[self.order.pk])
        data = {
            "status": OrderStatusChoices.PROCESSING # Invalid transition from PENDING to DELIVERED
        }
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, 403)
        
    def test_order_creation(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        data = {
            "order_items": [{
                "product": self.product.id,
                "quantity": 5, 
                "price": 200
            }]
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.count(), 3)
        
    def test_order_update_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        data = {
            "status": OrderStatusChoices.PROCESSING,
            "order_items": [{
                "product": self.product.id,
                "quantity": 5,
                "price": 120
            }]
        }
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.order2.refresh_from_db()
        self.assertEqual(self.order2.status, data["status"])
        self.assertEqual(self.order2.order_items.first().product.id, self.product.id)
        self.assertEqual(self.order2.order_items.first().quantity, data["order_items"][0]["quantity"])
        
    def test_order_delete_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(response.data)
        
    def test_list_orders_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)
        
    def test_list_orders_user(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        
    def test_retrieve_order(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        url = reverse("order-detail", args=[self.order2.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.order2.id)
        
    def test_retrieve_order_unauthorized(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        url = reverse("order-detail", args=[self.order2.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        
        
class ReviewViewSetTestCases(APITestCase):
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
        
        self.review = Review.objects.create(
            user=self.seller_user,
            product=self.product,
            rating=5,
            comment="this a the best product so far from this brand",
        )
        self.review_list = reverse("review-list")
        self.review_detail = reverse("review-detail", args=[self.review.id])
    
    def test_review_creation_user(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        data = {
            "product": self.product.id,
            "rating": 4,
            "comment": "One of the best product."
        }
        response = self.client.post(self.review_list, data, format="json")
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"], self.regular_user.id)
        self.assertEqual(response.data["comment"], data["comment"])
        self.assertFalse(response.data["is_approved"])
        
        self.assertEqual(Review.objects.count(), 2)
        
    def test_approve_review_by_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        data = {
            "is_approved": True
        }
        url = reverse('review-approve', args=[self.review.pk])
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, 200)
        self.review.refresh_from_db()
        self.assertTrue(self.review.is_approved)
        self.assertEqual(response.data["status"], "Review approved")
        
    def test_approve_review_unauthorize(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        data = {
            "is_approved": True
        }
        url = reverse('review-approve', args=[self.review.pk])
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, 403)
        
    def test_reject_review_by_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        url = reverse('review-reject', args=[self.review.pk])
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data["status"], "Review rejected")
        self.assertEqual(Review.objects.count(), 0)
            
    def test_reject_review_by_unauthorize(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.seller_jwt_token)
        
        url = reverse('review-reject', args=[self.review.pk])
        
        response = self.client.post(url)
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
        

class TransactionViewSetTestCases(APITestCase):
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
        
        self.order = Order.objects.create(
            user=self.regular_user,
            total_amount=1000.00
        )
        self.stripe_token = "visa_token"
        
        self.list_url = reverse("transaction-list")
        # self.detail_url = reverse("transaction-detail")
        self.detail_url = lambda pk: reverse("transaction-detail", args=[pk])
        
    @patch('stripe.Charge.create')   
    def test_create_transaction_success(self, mock_charge_create):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        mock_charge_create.return_value = {
            "id": "ch_764",
            "amount": 20000,
            "currency": "usd",
            "paid": True
        }
        data = {
            'order_id': self.order.id,
            'payment_method': 'stripe',
            'stripe_token': self.stripe_token,
            
        }
        
        response = self.client.post(self.list_url, data, format='json')
        transaction = Transaction.objects.first()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(transaction.order, self.order)
        self.assertEqual(transaction.payment_method, data["payment_method"])
        self.assertEqual(transaction.status, "completed")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        
    @patch("stripe.Charge.create")
    def test_create_failed_transaction(self, mock_charge_create):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        mock_charge_create.side_effect = stripe.error.CardError(
            "your card was declined.",
            code="card_declined",
            param=""
        )
        
        data = {
            "order_id": self.order.id,
            "payment_method": "stripe",
            "stripe_token": self.stripe_token,
            "status": "failed"
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertIn("An error occurred while processing your payment.", str(response.data["detail"]))
        self.assertEqual(len(mail.outbox), 1)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")
        
    @patch("stripe.Charge.create")
    def test_create_transaction_unexpected_error(self, mock_charge_create):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        mock_charge_create.side_effect = Exception("Unexpected error")
        
        data = {
            "order_id": self.order.id,
            "payment_method": "stripe",
            "stripe_token": self.stripe_token,
            "status": "failed"
        }
        
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("A system error occurred", str(response.data))
        self.assertEqual(len(mail.outbox), 1)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")
        
    def test_retrieve_user_transactions(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.regular_jwt_token)
        
        Transaction.objects.create(
            order=self.order,
            amount=200,
            payment_method="stripe",
            status="completed"
        )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["order"]["id"], self.order.id)
    
    def test_update_transaction_by_staff(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_jwt_token)
        
        transaction = Transaction.objects.create(
            order=self.order,
            amount=200,
            payment_method="stripe",
            status="pending"
        )
        data = {
            "status": "failed"
        }
        response = self.client.patch(self.detail_url(transaction.pk), data, format="json")
        print(response.data, response.status_code)
        # self.assertEqual(response.status_code, 200)
        