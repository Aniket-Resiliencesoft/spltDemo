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


__all__ = [
    'CreateOrderAPI',
    'GetWalletBalanceAPI',
    'GetWalletLedgerAPI',
    'InitiatePayoutAPI',
    'WebhookHandlerAPI',
]
