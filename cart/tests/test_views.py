
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.urls import reverse

from cart.models import Cart, CartItem
from products.models import Brand, Category, Product

User = get_user_model()


class GenerateToken:
    def __init__(self, user):
        self.user = user
        
    def generate_jwt_token(self):
        refresh = RefreshToken.for_user(self.user)
        return  str(refresh.access_token)
    
generate_token =  GenerateToken
     

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
        self.assertIn("cart_items", response.data)
        self.assertEqual(len(response.data["cart_items"]), 1)
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
