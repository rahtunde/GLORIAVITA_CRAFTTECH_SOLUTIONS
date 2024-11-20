from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APITestCase
from ecomhub.choices import TransactionStatusChoices, OrderStatusChoices
from ecomhub.models import Transaction, Order


User = get_user_model()


class UserSIgnalTestCase(APITestCase):
    
    def setUp(self) -> None:
        self.seller_group, _ = Group.objects.get_or_create(name="Seller")
        
    def test_seller_user_assigned_to_seller_group(self):
        seller_user = User.objects.create_user(
            email="testuser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="M",
            role="seller",
            phone_number="098235743",
        )
        self.assertTrue(seller_user.groups.filter(name="Seller").exists())
        
    def test_non_seller_user_not_assigned_to_seller_group(self):
        regular_user = User.objects.create_user(
            email="testuser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="F",
            role="buyer",
            phone_number="098235743",
        )
        self.assertFalse(regular_user.groups.filter(name="Seller").exists())
        
        
    def test_seller_user_removed_from_seller_group_when_role_changes(self):
        seller_user = User.objects.create_user(
            email="testuser@gmail.com",
            password="testuser_password",
            first_name="test1",
            last_name="test_last",
            gender="F",
            role="seller",
            phone_number="098235743",
        )
        self.assertTrue(seller_user.groups.filter(name="Seller").exists())
        seller_user.role = "buyer"
        seller_user.save()
        self.assertFalse(seller_user.groups.filter(name="Seller").exists())
