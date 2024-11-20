import hashlib

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {
            'password': {'write_only': True}
        }
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data.get('password'))
        return  super(UserSerializer, self).create(validated_data)       
        
    def update(self, instance, validated_data):
        if "password" in validated_data:
            validated_data["password"] = make_password(validated_data.get('password'))
        return super(UserSerializer, self).update(instance, validated_data)
    

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            "user_id": self.user.id
        })
        return data
    

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try: 
            # Find the user using email
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value
    
    def save(self, **kwargs):
        email = self.validated_data["email"]
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        reset_link = f"https://localhost:8000/reset-password/{uid}/{token}/"
        
        send_mail(
            'Password Reset',
            f'Click the following link to reset your password: {reset_link}',
            'noreply@localhost.com',
            [email],
            fail_silently=False,
        )
    


