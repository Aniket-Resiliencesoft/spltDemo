"""
Payment/Transaction API Views

Endpoints for managing event collection transactions.
"""
import razorpay
from rest_framework import status
from django.db.models import Q, Sum, Count
import traceback
import uuid
from decimal import Decimal

from common.api.base_api import BaseAuthenticatedAPI
from payments.models import EventCollectionTransaction, VendorPaymentTransaction
from events.models import Event
from payments.serializers import (
    EventCollectionTransactionGetSerializer,
    EventCollectionTransactionCreateSerializer,
    EventCollectionTransactionUpdateSerializer,
    EventCollectionTransactionListSerializer,
    VendorPaymentCreateSerializer,
    VendorPaymentGetSerializer,
)
from common.api.base_api import BaseAuthenticatedAPI
from payments.models import VendorPaymentTransaction

# from payments.utils.razorpay_client import razorpay_client as client 
from payments.utils.razorpay_client import razorpay_client

from spltmProject import settings


class TransactionListAPI(BaseAuthenticatedAPI):
    """
    GET: List all transactions with pagination and filters
    Supports filters: fromDate, toDate, status, search
    """
    
    def get(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Get pagination parameters
        page_no = int(request.query_params.get('pageNo', 1))
        page_size = int(request.query_params.get('pageSize', 10))
        
        # Get optional filters
        from_date = request.query_params.get('fromDate', '').strip()
        to_date = request.query_params.get('toDate', '').strip()
        status_filter = request.query_params.get('status', '').strip()
        search_filter = request.query_params.get('search', '').strip()
        
        # Base query
        query = EventCollectionTransaction.objects.filter(is_active=True)
        
        # Apply date filters
        if from_date:
            query = query.filter(transaction_date__gte=from_date)
        if to_date:
            query = query.filter(transaction_date__lte=to_date)
        
        # Apply status filter
        if status_filter:
            query = query.filter(status=status_filter)
        
        # Apply search filter (search in event title, user name, etc)
        if search_filter:
            query = query.filter(
                Q(event__title__icontains=search_filter) | 
                Q(user__full_name__icontains=search_filter) |
                Q(user__email__icontains=search_filter)
            )
        
        query = query.order_by('-transaction_date')
        
        # Get total count before pagination
        total_count = query.count()
        
        # Calculate offset
        offset = (page_no - 1) * page_size
        
        # Get transactions for this page
        transactions = query[offset:offset + page_size]
        
        # Serialize
        serializer = EventCollectionTransactionListSerializer(transactions, many=True)
        
        # Return paginated response with total record count
        return self.paginated_response(
            data=serializer.data,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
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


class UserPaymentsSummaryAPI(BaseAuthenticatedAPI):
    """
    GET: Returns all payments done by a user, total amount paid,
    and aggregated payments per event.
    """

    def get(self, request, user_id):
        # Auth: allow user themself or admin
        auth_error = self.require_self_or_admin(request, user_id)
        if auth_error:
            return auth_error

        # Optional pagination for transaction list
        page_no = int(request.query_params.get('pageNo', 1))
        page_size = int(request.query_params.get('pageSize', 100))

        # Base query: consider completed payments only
        query = EventCollectionTransaction.objects.filter(
            user_id=user_id,
            is_active=True,
            status='completed'
        ).order_by('-transaction_date')

        if not query.exists():
            return self.error_response(
                message="No completed payments found for this user",
                status_code=404
            )

        # Total amount across all events
        total_amount = query.aggregate(total=Sum('amount'))['total'] or 0

        # Aggregate per event
        per_event_qs = query.values('event_id', 'event__title').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')

      

        # Transactions (paginated)
        total_count = query.count()
        offset = (page_no - 1) * page_size
        transactions = query[offset:offset + page_size]
        serializer = EventCollectionTransactionListSerializer(transactions, many=True)

        data = {
            'user_id': user_id,
            'total_amount': str(total_amount),
            'transactions': serializer.data,
        }

        return self.paginated_response(
            data=data,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
            message="User payments summary retrieved successfully"
        )

class VendorPaymentCreateAPI(BaseAuthenticatedAPI):

    def post(self, request):
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error

        # Ensure the requesting user is available
        request_user_id = self.get_user_id(request)
        if not request_user_id:
            return self.error_response(
                message="Authentication required",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = VendorPaymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation failed", serializer.errors)

        # Ensure the requester is the event organiser
        event_id = serializer.validated_data.get('event')
        try:
            event_obj = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return self.error_response(
                message="Event not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # event.created_by is FK to User; compare IDs (cast to int to avoid string mismatches)
        try:
            organiser_id = int(getattr(event_obj.created_by, 'id', None))
            requester_id = int(request_user_id)
        except Exception:
            organiser_id = getattr(event_obj.created_by, 'id', None)
            requester_id = request_user_id

        if organiser_id != requester_id:
            return self.error_response(
                message="Only the event organiser can can pay to vender",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Force initiated_by to the requesting user (ignore client-supplied value)
        req_amount = serializer.validated_data.get('amount') or Decimal('0.00')

        total_collected = (
            EventCollectionTransaction.objects.filter(
                event_id=event_id,
                is_active=True,
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        )

        # Subtract already initiated/processed vendor payouts for this event
        processing_payouts = (
            VendorPaymentTransaction.objects.filter(
                event=event_id,
                is_active=True,
                status__in=("processing",)
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        )
        processed_payouts = (
            VendorPaymentTransaction.objects.filter(
                event=event_id,
                is_active=True,
                status__in=("processed",)
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        )

        available_for_payout = (Decimal(total_collected) - Decimal(processing_payouts) - Decimal(processed_payouts))
        if available_for_payout < Decimal('0.00'):
            available_for_payout = Decimal('0.00')

        if req_amount > available_for_payout:
            return self.error_response(
                message="Insufficient event funds",
                data={
                    "collected": str(total_collected),
                    "processing_payouts": str(processing_payouts),
                    "processed_payouts": str(processed_payouts),
                    "available": str(available_for_payout),
                    "requested": str(req_amount),
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        txn = serializer.save(initiated_by=request_user_id)

        return self.success_response(
            VendorPaymentGetSerializer(txn).data,
            "Vendor payment created",
            status.HTTP_201_CREATED
        )


class VendorPaymentListAPI(BaseAuthenticatedAPI):
    """
    GET: List vendor payment transactions with pagination and filters
    """

    def get(self, request):
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error

        page_no = int(request.query_params.get('pageNo', 1))
        page_size = int(request.query_params.get('pageSize', 10))

        status_filter = request.query_params.get('status', '').strip()
        event_filter = request.query_params.get('event', '').strip()
        search = request.query_params.get('search', '').strip()

        query = VendorPaymentTransaction.objects.filter(is_active=True)

        if status_filter:
            query = query.filter(status__iexact=status_filter)

        if event_filter:
            try:
                query = query.filter(event=int(event_filter))
            except Exception:
                pass

        if search:
            query = query.filter(
                Q(vendor_name__icontains=search) | Q(vendor_upi__icontains=search) | Q(purpose__icontains=search)
            )

        query = query.order_by('-created_at')

        total_count = query.count()
        offset = (page_no - 1) * page_size
        items = query[offset:offset + page_size]

        serializer = VendorPaymentGetSerializer(items, many=True)

        return self.paginated_response(
            data=serializer.data,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
            message="Vendor payouts retrieved successfully",
        )




class VendorPaymentPayoutAPI(BaseAuthenticatedAPI):
    """
    POST: Initiate RazorpayX payout for a vendor payment transaction
    """

    def post(self, request, transaction_id):
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error

        try:
            txn = VendorPaymentTransaction.objects.get(id=transaction_id, is_active=True)
        except VendorPaymentTransaction.DoesNotExist:
            return self.error_response(
                message="Transaction not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if txn.razorpay_payout_id:
            return self.error_response(
                message="Payout already initiated",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # validations
        if not txn.vendor_name:
            return self.error_response(
                message="Vendor name is missing",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if not txn.vendor_upi or "@" not in txn.vendor_upi:
            return self.error_response(
                message="Invalid or missing vendor UPI",
                data={"vendor_upi": txn.vendor_upi},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        account_number = getattr(settings, "RAZORPAY_ACCOUNT_NUMBER", None)
        if not account_number:
            return self.error_response(
                message="RAZORPAY_ACCOUNT_NUMBER not configured",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if txn.amount is None or txn.amount <= 0:
            return self.error_response(
                message="Invalid payout amount",
                data={"amount": str(txn.amount)},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            # ✅ Force correct full API path (prevents "api.razorpay.comcontacts" bug)
            contact = razorpay_client.post("/v1/contacts", {
                "name": str(txn.vendor_name).strip(),
                "type": "vendor"
            })
            contact_id = contact.get("id")
            if not contact_id:
                raise Exception(f"Contact creation failed: {contact}")

            fund_account = razorpay_client.post("/v1/fund_accounts", {
                "contact_id": contact_id,
                "account_type": "vpa",
                "vpa": {"address": txn.vendor_upi}
            })
            fund_account_id = fund_account.get("id")
            if not fund_account_id:
                raise Exception(f"Fund account creation failed: {fund_account}")

            payout_payload = {
                "account_number": account_number,
                "fund_account_id": fund_account_id,
                "amount": int(txn.amount * 100),
                "currency": "INR",
                "mode": "UPI",
                "purpose": "payout",
                "queue_if_low_balance": True
            }

            # ✅ Idempotency key (required for payouts in newer rules)
            idempotency_key = str(uuid.uuid4())

            # Many clients accept headers like this; if yours doesn't, see alt below
            payout = razorpay_client.post(
                "/v1/payouts",
                payout_payload,
                headers={"X-Payout-Idempotency": idempotency_key}
            )

            payout_id = payout.get("id")
            if not payout_id:
                raise Exception(f"Payout creation failed: {payout}")

            txn.razorpay_contact_id = contact_id
            txn.razorpay_fund_account_id = fund_account_id
            txn.razorpay_payout_id = payout_id
            txn.status = payout.get("status", "processing")
            txn.failure_reason = ""
            txn.save()

            return self.success_response(
                data=VendorPaymentGetSerializer(txn).data,
                message="Vendor payout initiated",
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            print("---- Razorpay payout exception ----")
            print("type:", type(e))
            print("str:", str(e))
            print("repr:", repr(e))
            print("args:", getattr(e, "args", None))
            traceback.print_exc()

            reason = str(e) or repr(e) or "Razorpay payout failed"

            txn.status = "failed"
            txn.failure_reason = reason[:255]
            txn.save()

            return self.error_response(
                message="Payout failed",
                data={"error": reason},
                status_code=status.HTTP_400_BAD_REQUEST
            )



class VendorPaymentStatusAPI(BaseAuthenticatedAPI):
    """
    GET: Get Razorpay payout status for a vendor payment transaction
    """

    def get(self, request, transaction_id):
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error

        try:
            txn = VendorPaymentTransaction.objects.get(id=transaction_id, is_active=True)
        except VendorPaymentTransaction.DoesNotExist:
            return self.error_response(
                message="Transaction not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # If you store Razorpay status directly: processing/processed/failed/reversed/queued
        is_final = txn.status in ("processed", "failed", "reversed")

        return self.success_response(
            data={
                "id": txn.id,
                "status": txn.status,
                "is_final": is_final,
                "failure_reason": txn.failure_reason or "",
                "razorpay_payout_id": txn.razorpay_payout_id or "",
                "updated_at": txn.updated_at,
            },
            message="Vendor payout status"
        )



class VendorPaymentRefreshStatusAPI(BaseAuthenticatedAPI):
    """
    POST: Refresh payout status from Razorpay and update DB
    """

    def post(self, request, transaction_id):
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error

        try:
            txn = VendorPaymentTransaction.objects.get(id=transaction_id, is_active=True)
        except VendorPaymentTransaction.DoesNotExist:
            return self.error_response(
                message="Transaction not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if not txn.razorpay_payout_id:
            return self.error_response(
                message="Payout not initiated yet",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            payout = razorpay_client.get(f"/v1/payouts/{txn.razorpay_payout_id}",{})
        except Exception as e:
            return self.error_response(
                message="Failed to fetch payout status from Razorpay",
                data={"error": str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        rp_status = payout.get("status", "")
        txn.status = rp_status or txn.status

        if rp_status == "failed":
            txn.failure_reason = (
                payout.get("failure_reason")
                or payout.get("status_details", {}).get("description")
                or "Payout failed"
            )
        elif rp_status:
            txn.failure_reason = ""

        txn.save()

        return self.success_response(
            data={
                "id": txn.id,
                "status": txn.status,
                "failure_reason": txn.failure_reason or "",
                "razorpay_payout_id": txn.razorpay_payout_id,
            },
            message="Payout status refreshed"
        )
