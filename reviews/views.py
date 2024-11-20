from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import Review
from .serializers import ReviewSerializer


from drf_yasg.utils import swagger_auto_schema


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(is_approved=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy", "approve", "reject"]:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
    
    @swagger_auto_schema(
        operation_description="Allow staff approve review.",
        request_body=ReviewSerializer,
        responses={200: ReviewSerializer, 400: "Bad request"}
    )   
    @action(detail=True, methods=["POST"], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        try:
            review = self.get_object()
            if review.is_approved:
                return Response({"status": "Review is already approved."}, status=status.HTTP_400_BAD_REQUEST)
            review.is_approved = True
            review.save()
            return Response({'status': "Review approved"}, status=status.HTTP_200_OK)
        except Exception as e:
            raise ValidationError(str(e))
    
    @swagger_auto_schema(
        operation_description="Allow staff reject review.",
        request_body=ReviewSerializer,
        responses={204: ReviewSerializer, 400: "Bad request"}
    )
    @action(detail=True, methods=["POST"], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        review = self.get_object()
        review.delete()
        return Response({"status": "Review rejected"}, status=204)
