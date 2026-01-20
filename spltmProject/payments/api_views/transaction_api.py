"""
Payment/Transaction API Views

Endpoints for managing event collection transactions.
"""

from rest_framework import status
from django.db.models import Q, Sum

from common.api.base_api import BaseAuthenticatedAPI
from payments.models import EventCollectionTransaction
from payments.serializers import (
    EventCollectionTransactionGetSerializer,
    EventCollectionTransactionCreateSerializer,
    EventCollectionTransactionUpdateSerializer,
    EventCollectionTransactionListSerializer,
)


class TransactionListAPI(BaseAuthenticatedAPI):
    """
    GET: List all transactions with pagination
    Filters by event, user, or status if provided in query params
    """
    
    def get(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Get pagination parameters
        page_no = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        # Get optional filters
        event_id = request.query_params.get('event_id')
        user_id = request.query_params.get('user_id')
        status_filter = request.query_params.get('status')
        transaction_type = request.query_params.get('transaction_type')
        
        # Base query
        query = EventCollectionTransaction.objects.filter(is_active=True)
        
        # Apply filters
        if event_id:
            query = query.filter(event_id=event_id)
        if user_id:
            query = query.filter(user_id=user_id)
        if status_filter:
            query = query.filter(status=status_filter)
        if transaction_type:
            query = query.filter(transaction_type=transaction_type)
        
        # Calculate offset
        offset = (page_no - 1) * page_size
        
        # Get transactions
        transactions = query[offset:offset + page_size]
        
        # Serialize
        serializer = EventCollectionTransactionListSerializer(transactions, many=True)
        
        # Return paginated response
        return self.paginated_response(
            data=serializer.data,
            page_no=page_no,
            page_size=page_size,
            message="Transactions retrieved successfully"
        )


class TransactionDetailAPI(BaseAuthenticatedAPI):
    """
    GET: Retrieve single transaction by ID
    """
    
    def get(self, request, transaction_id):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Get transaction
        try:
            transaction = EventCollectionTransaction.objects.get(
                id=transaction_id,
                is_active=True
            )
        except EventCollectionTransaction.DoesNotExist:
            return self.error_response(
                message="Transaction not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize
        serializer = EventCollectionTransactionGetSerializer(transaction)
        
        # Return response
        return self.success_response(
            data=serializer.data,
            message="Transaction retrieved successfully"
        )


class TransactionCreateAPI(BaseAuthenticatedAPI):
    """
    POST: Create a new transaction
    Requires authentication
    """
    
    def post(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Validate input
        serializer = EventCollectionTransactionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                message="Validation failed",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create transaction
        transaction = serializer.save()
        
        # Return created transaction
        response_serializer = EventCollectionTransactionGetSerializer(transaction)
        return self.success_response(
            data=response_serializer.data,
            message="Transaction created successfully",
            status_code=status.HTTP_201_CREATED
        )


class TransactionUpdateAPI(BaseAuthenticatedAPI):
    """
    PUT: Update transaction (full update)
    PATCH: Partial update transaction
    
    Only ADMIN can update transactions
    """
    
    def put(self, request, transaction_id):
        return self._update_transaction(request, transaction_id, partial=False)
    
    def patch(self, request, transaction_id):
        return self._update_transaction(request, transaction_id, partial=True)
    
    def _update_transaction(self, request, transaction_id, partial=False):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Check admin role
        admin_error = self.require_admin_role(request)
        if admin_error:
            return admin_error
        
        # Get transaction
        try:
            transaction = EventCollectionTransaction.objects.get(
                id=transaction_id,
                is_active=True
            )
        except EventCollectionTransaction.DoesNotExist:
            return self.error_response(
                message="Transaction not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Update transaction
        serializer = EventCollectionTransactionUpdateSerializer(
            transaction,
            data=request.data,
            partial=partial
        )
        
        if not serializer.is_valid():
            return self.error_response(
                message="Validation failed",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        
        # Return updated transaction
        response_serializer = EventCollectionTransactionGetSerializer(transaction)
        return self.success_response(
            data=response_serializer.data,
            message="Transaction updated successfully"
        )


class TransactionDeleteAPI(BaseAuthenticatedAPI):
    """
    DELETE: Soft delete transaction (set is_active=False)
    
    Only ADMIN can delete transactions
    """
    
    def delete(self, request, transaction_id):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Check admin role
        admin_error = self.require_admin_role(request)
        if admin_error:
            return admin_error
        
        # Get transaction
        try:
            transaction = EventCollectionTransaction.objects.get(
                id=transaction_id,
                is_active=True
            )
        except EventCollectionTransaction.DoesNotExist:
            return self.error_response(
                message="Transaction not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Soft delete
        transaction.is_active = False
        transaction.save()
        
        # Return success
        return self.success_response(
            message="Transaction deleted successfully"
        )


class EventTransactionSummaryAPI(BaseAuthenticatedAPI):
    """
    GET: Get transaction summary for an event
    Returns total collection, pending, completed stats
    """
    
    def get(self, request, event_id):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Get all transactions for this event
        transactions = EventCollectionTransaction.objects.filter(
            event_id=event_id,
            is_active=True
        )
        
        if not transactions.exists():
            return self.error_response(
                message="No transactions found for this event",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate statistics
        total_amount = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        
        completed = transactions.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        pending = transactions.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
        failed = transactions.filter(status='failed').aggregate(Sum('amount'))['amount__sum'] or 0
        
        summary = {
            'event_id': event_id,
            'total_amount': str(total_amount),
            'completed_amount': str(completed),
            'pending_amount': str(pending),
            'failed_amount': str(failed),
            'total_transactions': transactions.count(),
            'completed_count': transactions.filter(status='completed').count(),
            'pending_count': transactions.filter(status='pending').count(),
            'failed_count': transactions.filter(status='failed').count(),
            'unique_contributors': transactions.values('user_id').distinct().count(),
        }
        
        return self.success_response(
            data=summary,
            message="Event transaction summary"
        )


class UserTransactionHistoryAPI(BaseAuthenticatedAPI):
    """
    GET: Get transaction history for a user in an event
    Shows all transactions made by a user in a specific event
    """
    
    def get(self, request, event_id, user_id):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Get pagination parameters
        page_no = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        # Get transactions for user in event
        query = EventCollectionTransaction.objects.filter(
            event_id=event_id,
            user_id=user_id,
            is_active=True
        )
        
        if not query.exists():
            return self.error_response(
                message="No transactions found for this user in this event",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate offset
        offset = (page_no - 1) * page_size
        
        # Get transactions
        transactions = query[offset:offset + page_size]
        
        # Serialize
        serializer = EventCollectionTransactionListSerializer(transactions, many=True)
        
        # Get user total
        total = query.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Return response
        return self.paginated_response(
            data=serializer.data,
            page_no=page_no,
            page_size=page_size,
            message=f"User transaction history (Total: {total})"
        )
