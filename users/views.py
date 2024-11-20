from rest_framework import viewsets, permissions, status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .serializers import (UserSerializer, PasswordResetSerializer,
                          CustomTokenObtainPairSerializer)


from drf_yasg.utils import swagger_auto_schema

User = get_user_model()

  
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'list']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
    
    @swagger_auto_schema(
        operation_description="Allow new user to register.",
        request_body=UserSerializer,
        responses={201: UserSerializer, 400: "Bad request"}
    )
    @action(detail=False, methods=['POST'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,  status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Allow user's to change their password.",
        request_body=UserSerializer,
        responses={200: UserSerializer, 400: "Bad request"}
    )
    @action(detail=False, methods=["POST"], permission_classes=[permissions.AllowAny])
    def password_reset(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password reset e-mail has been sent."}, status=status.HTTP_200_OK)   
    
    @swagger_auto_schema(
        operation_description="Allow only staff (admin) change or update user role.",
        request_body=UserSerializer,
        responses={200: UserSerializer, 400: "Bad request"}
    )
    @action(detail=True, methods=["PATCH"], permission_classes=[permissions.IsAdminUser]) 
    def update_role(self, request, pk=None):
        user = self.get_object()
        role = request.data.get("role")
        roles = ["buyer", "seller", "admin"]
        if role not in roles:
            return Response({"detail": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)
        
        user.role = role
        user.save()
        return Response({"detail": f"Role updated to {role}"}, status=status.HTTP_200_OK)
        
        
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    create a custom class for the  token (login) to include email with its response 
    """
    serializer_class = CustomTokenObtainPairSerializer 
    