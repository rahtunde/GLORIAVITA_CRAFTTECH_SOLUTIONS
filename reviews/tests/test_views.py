
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.urls import reverse

from reviews.models import Review
from products.models import Brand, Category, Product

User = get_user_model()


class GenerateToken:
    def __init__(self, user):
        self.user = user
        
    def generate_jwt_token(self):
        refresh = RefreshToken.for_user(self.user)
        return  str(refresh.access_token)
    
generate_token =  GenerateToken
        
                
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
                
