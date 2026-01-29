"""
Payment API Views

Endpoints for payment operations:
- Create Razorpay orders
- Process webhooks
- Get wallet balance
- Initiate payouts
"""

import json
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from common.api.base_api import BaseAuthenticatedAPI
from payments.services import RazorpayPaymentService
from payments.models import WebhookLog

logger = logging.getLogger(__name__)


class CreateOrderAPI(BaseAuthenticatedAPI):
    """
    POST: Create Razorpay order for participant joining event
    
    Payload:
    {
        "event_id": 5,
        "amount": 1250.00,
        "description": "Participant payment"
    }
    
    Response:
    {
        "IsSuccess": true,
        "Message": "Order created successfully",
        "Data": {
            "order_id": 123,
            "razorpay_order_id": "order_123",
            "amount": 1250.00,
            "currency": "INR"
        }
    }
    """
    
    def post(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        try:
            event_id = request.data.get('event_id')
            amount = float(request.data.get('amount', 0))
            description = request.data.get('description', '')
            
            # Validate input
            if not event_id or amount <= 0:
                return self.error_response(
                    message="Invalid event_id or amount",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Create order
            service = RazorpayPaymentService()
            result = service.create_order(
                event_id=event_id,
                participant_id=request.jwt_user['user_id'],
                amount=amount,
                description=description
            )
            
            if result['IsSuccess']:
                return self.success_response(
                    data=result['Data'],
                    message=result['Message']
                )
            else:
                return self.error_response(
                    message=result['Message'],
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return self.error_response(
                message=f"Error: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyPaymentAPI(BaseAuthenticatedAPI):
    """
    POST: Verify payment signature and confirm payment
    
    Frontend sends payment details from Razorpay.
    Backend verifies signature using RAZORPAY_KEY_SECRET.
    Confirms payment validity.
    
    Payload:
    {
        "razorpay_order_id": "order_123",
        "razorpay_payment_id": "pay_123",
        "razorpay_signature": "signature_hash"
    }
    
    Response:
    {
        "IsSuccess": true,
        "Message": "Payment verified successfully",
        "Data": {
            "razorpay_order_id": "order_123",
            "razorpay_payment_id": "pay_123",
            "amount": 1250.00,
            "status": "verified"
        }
    }
    """
    
    def post(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        try:
            razorpay_order_id = request.data.get('razorpay_order_id')
            razorpay_payment_id = request.data.get('razorpay_payment_id')
            razorpay_signature = request.data.get('razorpay_signature')
            
            # Validate input
            if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
                return self.error_response(
                    message="razorpay_order_id, razorpay_payment_id, and razorpay_signature required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify payment signature
            service = RazorpayPaymentService()
            
            # Create signature string (order_id|payment_id)
            signature_string = f"{razorpay_order_id}|{razorpay_payment_id}"
            
            # Verify signature
            import hmac
            import hashlib
            from django.conf import settings
            
            expected_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                signature_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(expected_signature, razorpay_signature):
                logger.error(f"Invalid payment signature: {razorpay_order_id}")
                return self.error_response(
                    message="Payment verification failed - Invalid signature",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Get order from database
            from payments.models import RazorpayOrder
            razorpay_order = RazorpayOrder.objects.filter(
                razorpay_order_id=razorpay_order_id
            ).first()
            
            if not razorpay_order:
                return self.error_response(
                    message="Order not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            logger.info(f"Payment verified: {razorpay_payment_id} for order {razorpay_order_id}")
            
            return self.success_response(
                data={
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "amount": float(razorpay_order.amount),
                    "status": "verified"
                },
                message="Payment verified successfully"
            )
        
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return self.error_response(
                message=f"Error: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetWalletBalanceAPI(BaseAuthenticatedAPI):
    """
    GET: Get user's wallet balance
    
    Response:
    {
        "IsSuccess": true,
        "Message": "Wallet balance retrieved",
        "Data": {
            "balance": 5000.50,
            "user_id": 10
        }
    }
    """
    
    def get(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        try:
            service = RazorpayPaymentService()
            result = service.get_wallet_balance(request.jwt_user['user_id'])
            
            if result['IsSuccess']:
                return self.success_response(
                    data=result['Data'],
                    message=result['Message']
                )
            else:
                return self.error_response(
                    message=result['Message'],
                    status_code=status.HTTP_404_NOT_FOUND
                )
        
        except Exception as e:
            logger.error(f"Error getting wallet: {str(e)}")
            return self.error_response(
                message=f"Error: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetWalletLedgerAPI(BaseAuthenticatedAPI):
    """
    GET: Get user's wallet transaction history
    
    Query params:
    - limit: Number of records (default: 50)
    
    Response:
    {
        "IsSuccess": true,
        "Message": "Ledger retrieved",
        "Data": [
            {
                "id": 1,
                "transaction_type": "CREDIT",
                "amount": 1250.00,
                "reason": "PAYMENT_RECEIVED",
                "balance_before": 0.00,
                "balance_after": 1250.00,
                "description": "...",
                "created_at": "2026-01-28T10:30:00Z"
            }
        ]
    }
    """
    
    def get(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        try:
            limit = int(request.query_params.get('limit', 50))
            
            service = RazorpayPaymentService()
            result = service.get_wallet_ledger(
                request.jwt_user['user_id'],
                limit=limit
            )
            
            if result['IsSuccess']:
                return self.success_response(
                    data=result['Data'],
                    message=result['Message']
                )
            else:
                return self.error_response(
                    message=result['Message'],
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Error getting ledger: {str(e)}")
            return self.error_response(
                message=f"Error: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InitiatePayoutAPI(BaseAuthenticatedAPI):
    """
    POST: Initiate payout to event creator
    Admin can initiate for any event creator
    User can only initiate for their own events
    
    Payload:
    {
        "event_id": 5,
        "settlement_upi": "user@upi"
    }
    
    Response:
    {
        "IsSuccess": true,
        "Message": "Payout initiated successfully",
        "Data": {
            "payout_id": 1,
            "razorpay_payout_id": "payout_123",
            "amount": 5000.00
        }
    }
    """
    
    def post(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        try:
            event_id = request.data.get('event_id')
            settlement_upi = request.data.get('settlement_upi')
            vendor_id = request.data.get('vendor_id')
            
            # Validate input
            if not event_id or not settlement_upi:
                return self.error_response(
                    message="event_id and settlement_upi required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Authorization check
            if vendor_id and vendor_id != request.jwt_user['user_id']:
                if request.jwt_user['role'] != 'ADMIN':
                    return self.error_response(
                        message="Permission denied",
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            else:
                vendor_id = request.jwt_user['user_id']
            
            # Initiate payout
            service = RazorpayPaymentService()
            result = service.initiate_payout(
                event_id=event_id,
                vendor_id=vendor_id,
                settlement_upi=settlement_upi
            )
            
            if result['IsSuccess']:
                return self.success_response(
                    data=result['Data'],
                    message=result['Message']
                )
            else:
                return self.error_response(
                    message=result['Message'],
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Error initiating payout: {str(e)}")
            return self.error_response(
                message=f"Error: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class WebhookHandlerAPI(APIView):
    """
    POST: Handle all Razorpay webhooks
    
    Razorpay will POST to this endpoint for all events:
    - payment.captured
    - payment.failed
    - payout.processed
    - payout.failed
    
    CRITICAL: Verify signature before processing
    CRITICAL: Be idempotent (handle duplicate webhooks)
    """
    
    def post(self, request):
        try:
            # Get webhook signature from headers
            signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
            
            # Get raw body for signature verification
            webhook_body = request.body.decode('utf-8')
            
            # Parse payload
            payload = json.loads(webhook_body)
            
            # Get webhook ID
            webhook_id = payload.get('id')
            event_type = payload.get('event')
            
            logger.info(f"Webhook received: {event_type} - {webhook_id}")
            
            # Verify signature
            service = RazorpayPaymentService()
            signature_verified = service.verify_webhook_signature(
                webhook_body,
                signature
            )
            
            if not signature_verified:
                logger.error(f"Webhook signature verification failed: {webhook_id}")
                service.log_webhook(
                    webhook_id=webhook_id,
                    event_type=event_type,
                    payload=payload,
                    signature=signature,
                    signature_verified=False,
                    error_message="Signature verification failed"
                )
                return Response(
                    {"error": "Invalid signature"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Process webhook based on event type
            result = None
            
            if event_type == 'payment.captured':
                result = service.process_payment_captured_webhook(
                    payload.get('payload', {}).get('payment', {})
                )
            
            elif event_type == 'payment.failed':
                result = service.process_payment_failed_webhook(
                    payload.get('payload', {}).get('payment', {})
                )
            
            elif event_type == 'payout.processed':
                result = service.process_payout_processed_webhook(
                    payload.get('payload', {}).get('payout', {})
                )
            
            elif event_type == 'payout.failed':
                result = service.process_payout_failed_webhook(
                    payload.get('payload', {}).get('payout', {})
                )
            
            else:
                logger.warning(f"Unknown webhook event type: {event_type}")
                result = {
                    "IsSuccess": False,
                    "Message": "Unknown event type"
                }
            
            # Log webhook
            service.log_webhook(
                webhook_id=webhook_id,
                event_type=event_type,
                payload=payload,
                signature=signature,
                signature_verified=True,
                processed=True,
                processing_status="SUCCESS" if result['IsSuccess'] else "FAILED",
                error_message=None if result['IsSuccess'] else result.get('Message')
            )
            
            logger.info(f"Webhook processed: {event_type} - Status: {result['IsSuccess']}")
            
            return Response(
                {"status": "received"},
                status=status.HTTP_200_OK
            )
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            return Response(
                {"error": "Invalid JSON"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SettleToVendorAPI(BaseAuthenticatedAPI):
    """
    POST: Vendor requests settlement from owner's collected amount
    
    Vendor provides their UPI/Bank details.
    Backend initiates payout using OWNER's account number.
    Amount deducted from owner's collected balance.
    
    Payload:
    {
        "event_id": 5,
        "settlement_upi": "vendor@upi",
        "amount": 500.00  (optional - if not provided, entire remaining amount)
    }
    
    Response:
    {
        "IsSuccess": true,
        "Message": "Settlement initiated successfully",
        "Data": {
            "settlement_id": 1,
            "razorpay_payout_id": "payout_123456",
            "amount": 500.00,
            "vendor_upi": "vendor@upi",
            "total_collected": 2000.00,
            "total_settled": 500.00,
            "remaining_amount": 1500.00
        }
    }
    """
    
    def post(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        try:
            event_id = request.data.get('event_id')
            settlement_upi = request.data.get('settlement_upi')
            amount = request.data.get('amount')  # Optional
            
            # Validate input
            if not event_id or not settlement_upi:
                return self.error_response(
                    message="event_id and settlement_upi required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate amount if provided
            if amount is not None:
                try:
                    amount = float(amount)
                    if amount <= 0:
                        raise ValueError("Amount must be > 0")
                except (ValueError, TypeError):
                    return self.error_response(
                        message="Invalid amount",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            
            # Request settlement
            service = RazorpayPaymentService()
            result = service.request_settlement(
                event_id=event_id,
                vendor_id=request.jwt_user['user_id'],
                settlement_upi=settlement_upi,
                amount=amount
            )
            
            if result['IsSuccess']:
                return self.success_response(
                    data=result['Data'],
                    message=result['Message']
                )
            else:
                return self.error_response(
                    message=result['Message'],
                    data=result.get('Data'),
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Error requesting settlement: {str(e)}")
            return self.error_response(
                message=f"Error: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class GetSettlementSummaryAPI(BaseAuthenticatedAPI):
    """
    GET: Get settlement summary for an event
    
    Shows:
    - Total collected from all participants
    - Total settled to vendors
    - Remaining amount available
    - List of all settlements
    
    Query params:
    - event_id: Event ID (required)
    
    Response:
    {
        "IsSuccess": true,
        "Message": "Settlement summary retrieved",
        "Data": {
            "total_collected": 2000.00,
            "total_settled": 1000.00,
            "remaining_amount": 1000.00,
            "settlements": [
                {
                    "id": 1,
                    "vendor": "John Doe",
                    "amount": 500.00,
                    "description": "Accommodation",
                    "date": "2026-01-29T10:30:00Z"
                }
            ]
        }
    }
    """
    
    def get(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        try:
            event_id = request.query_params.get('event_id')
            
            if not event_id:
                return self.error_response(
                    message="event_id parameter required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            service = RazorpayPaymentService()
            result = service.get_event_settlement_summary(event_id)
            
            if result['IsSuccess']:
                return self.success_response(
                    data=result['Data'],
                    message=result['Message']
                )
            else:
                return self.error_response(
                    message=result['Message'],
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Error getting settlement summary: {str(e)}")
            return self.error_response(
                message=f"Error: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


__all__ = [
    'CreateOrderAPI',
    'VerifyPaymentAPI',
    'GetWalletBalanceAPI',
    'GetWalletLedgerAPI',
    'InitiatePayoutAPI',
    'WebhookHandlerAPI',
    'SettleToVendorAPI',
    'GetSettlementSummaryAPI',
]
