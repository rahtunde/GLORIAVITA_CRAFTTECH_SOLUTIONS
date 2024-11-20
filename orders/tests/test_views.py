
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.urls import reverse

from orders.choices import OrderStatusChoices
from orders.models import Order, OrderItem
from products.models import Brand, Product, Category

User = get_user_model()


class GenerateToken:
    def __init__(self, user):
        self.user = user
        
    def generate_jwt_token(self):
        refresh = RefreshToken.for_user(self.user)
        return  str(refresh.access_token)
    
generate_token =  GenerateToken
        



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
