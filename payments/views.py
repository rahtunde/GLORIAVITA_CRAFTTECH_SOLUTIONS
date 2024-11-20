from rest_framework import viewsets, status
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from django.db import transaction

from .choices import OrderStatusChoices, TransactionStatusChoices

from .models import Transaction
from .serializers import TransactionSerializer


from drf_yasg.utils import swagger_auto_schema

User = get_user_model()



class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Transaction-related actions including listing, creating, and updating transactions.
    """
    queryset = Transaction.objects.select_related("order").order_by("-transaction_date")
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        """
        Returns queryset for staff or filters transactions by the logged-in user.
        """
        user = self.request.user 
        
        # Only fetch the current user's transactions unless the user is staff
        if user.is_staff:
            return Transaction.objects.select_related("order").order_by("-transaction_date")
        return Transaction.objects.filter(order__user=user).select_related("order").order_by("-transaction_date")
     
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Handle transaction creation with atomic operations to ensure data consistency.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Perform the transaction creation (in serializer's `create` method)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Handle transaction updates, including status changes.
        Only staff members are allowed to update the transaction status.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check if the user is staff before allowing status update
        if 'status' in request.data and not request.user.is_staff:
            return Response({"error": "Only staff members can update transaction status."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Perform the update 
        self.perform_update(serializer)
        
        # Update order status if transaction status changes
        if 'status' in serializer.validated_data:
            self._update_order_status(instance, serializer.validated_data["status"])
        
        return Response(serializer.data)
    @swagger_auto_schema(
        operation_description="Helper function to update transaction status.",
        request_body=TransactionSerializer,
        responses={200: TransactionSerializer, 400: "Bad request"}
    )  
    def _update_order_status(self, transaction, new_status):
        """
        Update the order status based on the transaction status changes.
        """
        order = transaction.order
        if new_status == TransactionStatusChoices.COMPLETED:
            order.status = OrderStatusChoices.PAID
        elif new_status == TransactionStatusChoices.FAILED:
            order.status = OrderStatusChoices.FAILED
        order.save()
        
    def perform_create(self, serializer):
        """
        Override perform_create to use atomic transactions.
        """
        with transaction.atomic():
            serializer.save()
    
    def perform_update(self, serializer):
        """
        Override perform_update to ensure atomic transactions during updates.
        """
        with transaction.atomic():
            serializer.save()
    