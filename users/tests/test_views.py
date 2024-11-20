import hashlib
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail

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
        
        
    def test_reset_password(self):
        url = reverse("users-password-reset")
        
        data = {
            "email": self.user.email
        }
        
        response = self.client.post(url, data, format="json")
        print(response.data)
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
        print(response.data)
        # print(User.objects.values_list())
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user_id"], user.id)
        
    def test_user_login_failure(self):
        url = reverse("login")
        data = {"email": "testuser@example.com", "password": "pass23"}
        
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 401)
        
