"""
Payment Service Module - Razorpay Integration

Handles all payment operations with Razorpay:
- Creating orders
- Processing webhooks
- Managing virtual wallets
- Processing payouts
"""

import hmac
import hashlib
import json
import logging
from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
import razorpay
from django.conf import settings

from payments.models import (
    RazorpayOrder,
    UserWallet,
    WalletLedger,
    RazorpayPayout,
    WebhookLog,
    EventCollectionTransaction
)
from accounts.models import User
from events.models import Event
from events.utils import compute_split

logger = logging.getLogger(__name__)


class RazorpayPaymentService:
    """
    Service class for all Razorpay payment operations.
    Handles: Orders, Payments, Webhooks, Payouts
    """
    
    def __init__(self):
        """Initialize Razorpay client"""
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    
    # =====================================================
    # 1. ORDER CREATION
    # =====================================================
    
    def create_order(self, event_id, participant_id, amount, description=""):
        """
        Create Razorpay order when user joins event.
        
        Args:
            event_id: Event ID
            participant_id: User ID of participant
            amount: Amount in INR
            description: Order description
        
        Returns:
            {
                "IsSuccess": True/False,
                "Message": "...",
                "Data": {...}
            }
        """
        try:
            # Validate event and participant
            event = Event.objects.get(id=event_id, is_active=True)
            participant = User.objects.get(id=participant_id, is_active=True)
            
            # Check if order already exists
            existing_order = RazorpayOrder.objects.filter(
                event=event,
                participant=participant
            ).first()
            
            if existing_order and existing_order.status == 'PAID':
                return {
                    "IsSuccess": False,
                    "Message": "User already paid for this event",
                    "Data": None
                }
            
            # Create Razorpay order
            razorpay_order = self.client.order.create({
                'amount': int(amount * 100),  # Convert to paise
                'currency': 'INR',
                'receipt': f"event_{event_id}_user_{participant_id}",
                'notes': {
                    'event_id': event_id,
                    'participant_id': participant_id,
                    'participant_name': participant.full_name,
                    'event_name': event.title
                }
            })
            
            # Store order in database
            order_obj = RazorpayOrder.objects.create(
                event=event,
                participant=participant,
                razorpay_order_id=razorpay_order['id'],
                amount=Decimal(str(amount)),
                currency='INR',
                receipt=razorpay_order.get('receipt'),
                notes=razorpay_order.get('notes', {})
            )
            
            logger.info(f"Order created: {razorpay_order['id']} for event {event_id}")
            
            return {
                "IsSuccess": True,
                "Message": "Order created successfully",
                "Data": {
                    'order_id': order_obj.id,
                    'razorpay_order_id': razorpay_order['id'],
                    'amount': float(amount),
                    'currency': 'INR'
                }
            }
        
        except Event.DoesNotExist:
            return {
                "IsSuccess": False,
                "Message": "Event not found",
                "Data": None
            }
        except User.DoesNotExist:
            return {
                "IsSuccess": False,
                "Message": "User not found",
                "Data": None
            }
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return {
                "IsSuccess": False,
                "Message": f"Error creating order: {str(e)}",
                "Data": None
            }
    
    # =====================================================
    # 2. WEBHOOK VERIFICATION & PROCESSING
    # =====================================================
    
    def verify_webhook_signature(self, webhook_body, signature):
        """
        Verify Razorpay webhook signature.
        
        Args:
            webhook_body: Raw webhook body (string)
            signature: Signature from header
        
        Returns:
            Boolean - True if valid
        """
        try:
            expected_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                webhook_body.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        
        except Exception as e:
            logger.error(f"Error verifying webhook: {str(e)}")
            return False
    
    @transaction.atomic
    def process_payment_captured_webhook(self, payload):
        """
        Handle payment.captured webhook.
        Credit event creator's wallet.
        
        Args:
            payload: Webhook payload
        
        Returns:
            {
                "IsSuccess": True/False,
                "Message": "...",
                "Data": {...}
            }
        """
        try:
            payment_id = payload.get('id')
            order_id = payload.get('order_id')
            amount = Decimal(str(payload.get('amount', 0))) / 100  # Convert from paise
            
            # Find order
            razorpay_order = RazorpayOrder.objects.filter(
                razorpay_order_id=order_id
            ).first()
            
            if not razorpay_order:
                logger.error(f"Order not found: {order_id}")
                return {
                    "IsSuccess": False,
                    "Message": "Order not found",
                    "Data": None
                }
            
            # Check if already processed (idempotency)
            if razorpay_order.status == 'PAID':
                logger.warning(f"Order already paid: {order_id}")
                return {
                    "IsSuccess": True,
                    "Message": "Order already processed",
                    "Data": {"order_id": order_id}
                }
            
            # Update order
            razorpay_order.razorpay_payment_id = payment_id
            razorpay_order.status = 'PAID'
            razorpay_order.webhook_received = True
            razorpay_order.webhook_verified = True
            razorpay_order.save()
            
            # Get event creator (vendor)
            vendor = razorpay_order.event.created_by

            # Compute split based on event config (uses Decimal-safe logic)
            try:
                split = compute_split(razorpay_order.event.event_amount, razorpay_order.event.persons_count)
                per_head = split['per_head']
                admin_charge_per_head = split['admin_charge_per_head']
                final_per_head = split['final_per_head']
            except Exception:
                # Fallback: treat entire amount as vendor amount
                per_head = amount
                admin_charge_per_head = Decimal('0.00')
                final_per_head = amount

            # If captured amount doesn't match expected final_per_head, log a warning
            if amount != final_per_head:
                logger.warning(
                    f"Captured amount {amount} differs from expected final_per_head {final_per_head} for order {order_id}"
                )

            # Credit vendor wallet with base per_head
            self._credit_wallet(
                user=vendor,
                amount=per_head,
                reason='PAYMENT_RECEIVED',
                event_id=razorpay_order.event.id,
                razorpay_order_id=order_id,
                razorpay_payment_id=payment_id,
                description=f"Payment (base) from {razorpay_order.participant.full_name} for {razorpay_order.event.title}"
            )

            # Credit admin commission to configured platform admin user if available
            admin_user = None
            admin_user_id = getattr(settings, 'PLATFORM_ADMIN_USER_ID', None)
            admin_user_email = getattr(settings, 'PLATFORM_ADMIN_EMAIL', None)

            try:
                if admin_user_id:
                    admin_user = User.objects.filter(id=admin_user_id, is_active=True).first()
                elif admin_user_email:
                    admin_user = User.objects.filter(email=admin_user_email, is_active=True).first()
            except Exception:
                admin_user = None

            if admin_charge_per_head > Decimal('0.00'):
                if admin_user:
                    # Credit admin user wallet
                    self._credit_wallet(
                        user=admin_user,
                        amount=admin_charge_per_head,
                        reason='ADMIN_COMMISSION',
                        event_id=razorpay_order.event.id,
                        razorpay_order_id=order_id,
                        razorpay_payment_id=payment_id,
                        description=f"Admin commission from {razorpay_order.participant.full_name} for {razorpay_order.event.title}"
                    )
                else:
                    # Fallback: if no admin user configured, credit the vendor with the admin portion
                    # (keeps money accounted for until admin account is configured)
                    self._credit_wallet(
                        user=vendor,
                        amount=admin_charge_per_head,
                        reason='ADMIN_COMMISSION_FALLBACK',
                        event_id=razorpay_order.event.id,
                        razorpay_order_id=order_id,
                        razorpay_payment_id=payment_id,
                        description=f"Admin commission fallback credited to vendor for {razorpay_order.event.title}"
                    )

            logger.info(f"Payment captured: {payment_id}, credited vendor {vendor.id}")

            return {
                "IsSuccess": True,
                "Message": "Payment processed successfully",
                "Data": {
                    "order_id": order_id,
                    "payment_id": payment_id,
                    "amount": float(amount),
                    "split": {
                        "per_head": str(per_head),
                        "admin_charge_per_head": str(admin_charge_per_head),
                        "final_per_head": str(final_per_head)
                    }
                }
            }
        
        except Exception as e:
            logger.error(f"Error processing payment webhook: {str(e)}")
            return {
                "IsSuccess": False,
                "Message": f"Error processing payment: {str(e)}",
                "Data": None
            }
    
    @transaction.atomic
    def process_payment_failed_webhook(self, payload):
        """
        Handle payment.failed webhook.
        Mark order as failed (no wallet changes).
        
        Args:
            payload: Webhook payload
        
        Returns:
            Response dict
        """
        try:
            payment_id = payload.get('id')
            order_id = payload.get('order_id')
            
            razorpay_order = RazorpayOrder.objects.filter(
                razorpay_order_id=order_id
            ).first()
            
            if razorpay_order:
                razorpay_order.status = 'FAILED'
                razorpay_order.webhook_received = True
                razorpay_order.save()
                
                logger.info(f"Payment failed: {payment_id}")
            
            return {
                "IsSuccess": True,
                "Message": "Payment failed webhook processed",
                "Data": {"order_id": order_id}
            }
        
        except Exception as e:
            logger.error(f"Error processing failed payment webhook: {str(e)}")
            return {
                "IsSuccess": False,
                "Message": f"Error: {str(e)}",
                "Data": None
            }
    
    # =====================================================
    # 3. WALLET OPERATIONS
    # =====================================================
    
    def get_wallet_balance(self, user_id):
        """Get current wallet balance for user"""
        try:
            wallet = UserWallet.objects.get(user_id=user_id)
            return {
                "IsSuccess": True,
                "Message": "Wallet balance retrieved",
                "Data": {
                    "balance": float(wallet.balance),
                    "user_id": user_id
                }
            }
        except UserWallet.DoesNotExist:
            return {
                "IsSuccess": False,
                "Message": "Wallet not found",
                "Data": None
            }
    
    def get_wallet_ledger(self, user_id, limit=50):
        """Get wallet transaction history"""
        try:
            ledger_entries = WalletLedger.objects.filter(
                user_id=user_id
            ).order_by('-created_at')[:limit]
            
            data = [
                {
                    'id': entry.id,
                    'transaction_type': entry.transaction_type,
                    'amount': float(entry.amount),
                    'reason': entry.reason,
                    'balance_before': float(entry.balance_before),
                    'balance_after': float(entry.balance_after),
                    'description': entry.description,
                    'created_at': entry.created_at.isoformat()
                }
                for entry in ledger_entries
            ]
            
            return {
                "IsSuccess": True,
                "Message": "Ledger retrieved",
                "Data": data
            }
        except Exception as e:
            logger.error(f"Error retrieving ledger: {str(e)}")
            return {
                "IsSuccess": False,
                "Message": f"Error: {str(e)}",
                "Data": None
            }
    
    def _credit_wallet(self, user, amount, reason, event_id=None, 
                      razorpay_order_id=None, razorpay_payment_id=None,
                      razorpay_payout_id=None, razorpay_refund_id=None,
                      description="", idempotency_key=None):
        """
        Credit user wallet and create ledger entry.
        
        INTERNAL METHOD - Called by webhook processors
        """
        try:
            # Get or create wallet
            wallet, _ = UserWallet.objects.get_or_create(user=user)
            
            # Check idempotency
            if idempotency_key:
                existing = WalletLedger.objects.filter(
                    idempotency_key=idempotency_key
                ).first()
                if existing:
                    logger.warning(f"Duplicate ledger entry detected: {idempotency_key}")
                    return existing
            
            # Record balance before
            balance_before = wallet.balance
            
            # Update wallet
            wallet.balance += amount
            wallet.save()
            
            # Create ledger entry
            ledger = WalletLedger.objects.create(
                user=user,
                transaction_type='CREDIT',
                amount=amount,
                reason=reason,
                event_id=event_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_payout_id=razorpay_payout_id,
                razorpay_refund_id=razorpay_refund_id,
                balance_before=balance_before,
                balance_after=wallet.balance,
                description=description,
                idempotency_key=idempotency_key
            )
            
            logger.info(f"Wallet credited: {user.id}, amount: {amount}")
            return ledger
        
        except Exception as e:
            logger.error(f"Error crediting wallet: {str(e)}")
            raise
    
    def _debit_wallet(self, user, amount, reason, event_id=None,
                     razorpay_payout_id=None, razorpay_refund_id=None,
                     description="", idempotency_key=None):
        """
        Debit user wallet and create ledger entry.
        
        INTERNAL METHOD - Called by payout processors
        """
        try:
            wallet = UserWallet.objects.get(user=user)
            
            # Check idempotency
            if idempotency_key:
                existing = WalletLedger.objects.filter(
                    idempotency_key=idempotency_key
                ).first()
                if existing:
                    logger.warning(f"Duplicate ledger entry detected: {idempotency_key}")
                    return existing
            
            # Validate sufficient balance
            if wallet.balance < amount:
                raise ValueError("Insufficient wallet balance")
            
            # Record balance before
            balance_before = wallet.balance
            
            # Update wallet
            wallet.balance -= amount
            wallet.save()
            
            # Create ledger entry
            ledger = WalletLedger.objects.create(
                user=user,
                transaction_type='DEBIT',
                amount=amount,
                reason=reason,
                event_id=event_id,
                razorpay_payout_id=razorpay_payout_id,
                razorpay_refund_id=razorpay_refund_id,
                balance_before=balance_before,
                balance_after=wallet.balance,
                description=description,
                idempotency_key=idempotency_key
            )
            
            logger.info(f"Wallet debited: {user.id}, amount: {amount}")
            return ledger
        
        except Exception as e:
            logger.error(f"Error debiting wallet: {str(e)}")
            raise
    
    # =====================================================================
    # 4. PAYOUT OPERATIONS
    # =====================================================================
    
    def initiate_payout(self, event_id, vendor_id, settlement_upi=None):
        """
        Initiate payout to event creator after event completion.
        
        Args:
            event_id: Event ID
            vendor_id: Event creator (vendor) ID
            settlement_upi: UPI ID for payout
        
        Returns:
            Response dict
        """
        try:
            event = Event.objects.get(id=event_id, is_active=True)
            vendor = User.objects.get(id=vendor_id, is_active=True)
            wallet = UserWallet.objects.get(user=vendor)
            
            # Check if payout already initiated
            existing_payout = RazorpayPayout.objects.filter(
                event=event,
                vendor=vendor
            ).exclude(status='FAILED').first()
            
            if existing_payout:
                return {
                    "IsSuccess": False,
                    "Message": "Payout already initiated for this event",
                    "Data": None
                }
            
            # Validate balance
            if wallet.balance <= 0:
                return {
                    "IsSuccess": False,
                    "Message": "Insufficient wallet balance",
                    "Data": None
                }
            
            payout_amount = wallet.balance
            
            # Create or get Razorpay contact
            contact = self._get_or_create_razorpay_contact(vendor)
            
            # Create fund account
            fund_account = self._create_razorpay_fund_account(
                contact['id'],
                settlement_upi
            )
            
            # Create payout
            razorpay_payout = self.client.payout.create({
                'account_number': settings.RAZORPAY_ACCOUNT_NUMBER,
                'fund_account_id': fund_account['id'],
                'amount': int(payout_amount * 100),  # Convert to paise
                'currency': 'INR',
                'mode': 'UPI',
                'purpose': 'payout',
                'queue_if_low_balance': True,
                'reference_id': f"payout_event_{event_id}_vendor_{vendor_id}",
                'notes': {
                    'event_id': event_id,
                    'vendor_id': vendor_id,
                    'vendor_name': vendor.full_name
                }
            })
            
            # Store payout in database
            payout_obj = RazorpayPayout.objects.create(
                event=event,
                vendor=vendor,
                razorpay_payout_id=razorpay_payout['id'],
                razorpay_contact_id=contact['id'],
                razorpay_fund_account_id=fund_account['id'],
                amount=payout_amount,
                settlement_type='UPI',
                settlement_upi=settlement_upi,
                status='INITIATED'
            )
            
            logger.info(f"Payout initiated: {razorpay_payout['id']} for vendor {vendor_id}")
            
            return {
                "IsSuccess": True,
                "Message": "Payout initiated successfully",
                "Data": {
                    'payout_id': payout_obj.id,
                    'razorpay_payout_id': razorpay_payout['id'],
                    'amount': float(payout_amount)
                }
            }
        
        except Exception as e:
            logger.error(f"Error initiating payout: {str(e)}")
            return {
                "IsSuccess": False,
                "Message": f"Error: {str(e)}",
                "Data": None
            }
    
    def _get_or_create_razorpay_contact(self, user):
        """Get or create Razorpay contact for user"""
        wallet = UserWallet.objects.get(user=user)
        
        if wallet.razorpay_customer_id:
            return self.client.customer.fetch(wallet.razorpay_customer_id)
        
        # Create new contact
        contact = self.client.contact.create({
            'name': user.full_name,
            'email': user.email,
            'contact': user.contact_no,
            'type': 'vendor'
        })
        
        # Update wallet with contact ID
        wallet.razorpay_customer_id = contact['id']
        wallet.save()
        
        return contact
    
    def _create_razorpay_fund_account(self, contact_id, upi_id):
        """Create fund account for payout"""
        return self.client.fund_account.create({
            'contact_id': contact_id,
            'account_type': 'vpa',
            'vpa': {
                'address': upi_id
            }
        })
    
    @transaction.atomic
    def process_payout_processed_webhook(self, payload):
        """
        Handle payout.processed webhook.
        Debit vendor wallet after successful payout.
        """
        try:
            payout_id = payload.get('id')
            amount = Decimal(str(payload.get('amount', 0))) / 100
            
            payout = RazorpayPayout.objects.filter(
                razorpay_payout_id=payout_id
            ).first()
            
            if not payout:
                logger.error(f"Payout not found: {payout_id}")
                return {
                    "IsSuccess": False,
                    "Message": "Payout not found",
                    "Data": None
                }
            
            # Debit vendor wallet
            self._debit_wallet(
                user=payout.vendor,
                amount=amount,
                reason='PAYOUT_SUCCESS',
                razorpay_payout_id=payout_id,
                description=f"Payout completed for event {payout.event.title}"
            )
            
            # Update payout status
            payout.status = 'PROCESSED'
            payout.webhook_received = True
            payout.webhook_verified = True
            payout.save()
            
            logger.info(f"Payout processed: {payout_id}")
            
            return {
                "IsSuccess": True,
                "Message": "Payout processed successfully",
                "Data": {"payout_id": payout_id}
            }
        
        except Exception as e:
            logger.error(f"Error processing payout webhook: {str(e)}")
            return {
                "IsSuccess": False,
                "Message": f"Error: {str(e)}",
                "Data": None
            }
    
    @transaction.atomic
    def process_payout_failed_webhook(self, payload):
        """
        Handle payout.failed webhook.
        Credit vendor wallet (refund) on failed payout.
        """
        try:
            payout_id = payload.get('id')
            amount = Decimal(str(payload.get('amount', 0))) / 100
            
            payout = RazorpayPayout.objects.filter(
                razorpay_payout_id=payout_id
            ).first()
            
            if not payout:
                logger.error(f"Payout not found: {payout_id}")
                return {
                    "IsSuccess": False,
                    "Message": "Payout not found",
                    "Data": None
                }
            
            # Credit vendor wallet (refund)
            self._credit_wallet(
                user=payout.vendor,
                amount=amount,
                reason='PAYOUT_FAILED',
                razorpay_payout_id=payout_id,
                description=f"Payout failed for event {payout.event.title} - Amount refunded"
            )
            
            # Update payout status
            payout.status = 'FAILED'
            payout.failure_reason = payload.get('failure_reason', 'Unknown')
            payout.webhook_received = True
            payout.webhook_verified = True
            payout.save()
            
            logger.info(f"Payout failed and refunded: {payout_id}")
            
            return {
                "IsSuccess": True,
                "Message": "Payout failed - Amount refunded to wallet",
                "Data": {"payout_id": payout_id}
            }
        
        except Exception as e:
            logger.error(f"Error processing payout failed webhook: {str(e)}")
            return {
                "IsSuccess": False,
                "Message": f"Error: {str(e)}",
                "Data": None
            }
    
    # =====================================================================
    # 5. WEBHOOK LOGGING
    # =====================================================================
    
    def log_webhook(self, webhook_id, event_type, payload, signature, 
                   signature_verified=False, processed=False, 
                   processing_status=None, error_message=None):
        """Log webhook for audit trail and debugging"""
        try:
            WebhookLog.objects.create(
                webhook_id=webhook_id,
                event_type=event_type,
                payload=payload,
                signature=signature,
                signature_verified=signature_verified,
                processed=processed,
                processing_status=processing_status,
                error_message=error_message,
                razorpay_entity_id=payload.get('entity', {}).get('id')
            )
        except Exception as e:
            logger.error(f"Error logging webhook: {str(e)}")    
    # =====================================================================
    # 6. EVENT SETTLEMENT (Vendor requests, Owner's account pays)
    # =====================================================================
    
    def request_settlement(self, event_id, vendor_id, settlement_upi, amount=None):
        """
        Vendor requests settlement from owner's collected amount.
        Uses owner's account number (RAZORPAY_ACCOUNT_NUMBER) for payout.
        
        Args:
            event_id: Event ID
            vendor_id: Vendor (event creator) ID
            settlement_upi: Vendor's UPI ID
            amount: Specific amount (optional, if None = all remaining collected)
        
        Returns:
            {
                "IsSuccess": True/False,
                "Message": "...",
                "Data": {...}
            }
        """
        try:
            from payments.models import EventSettlement
            
            event = Event.objects.get(id=event_id, is_active=True)
            vendor = User.objects.get(id=vendor_id, is_active=True)
            
            # Validate vendor is event creator
            if event.created_by.id != vendor_id:
                return {
                    "IsSuccess": False,
                    "Message": "Only event creator can request settlement",
                    "Data": None
                }
            
            # Get total collected for event
            total_collected = EventCollectionTransaction.objects.filter(
                event_id=event_id,
                status='completed'
            ).aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
            
            # Get total already settled for event
            total_settled = EventSettlement.objects.filter(
                event_id=event_id,
                status='completed'
            ).aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
            
            # Calculate remaining available
            remaining = total_collected - total_settled
            
            # Determine settlement amount
            if amount is None:
                settlement_amount = remaining
            else:
                settlement_amount = Decimal(str(amount))
            
            # Validate amount
            if settlement_amount <= 0:
                return {
                    "IsSuccess": False,
                    "Message": "Settlement amount must be greater than 0",
                    "Data": None
                }
            
            if settlement_amount > remaining:
                return {
                    "IsSuccess": False,
                    "Message": f"Cannot settle ₹{settlement_amount}. Remaining available: ₹{remaining}",
                    "Data": {
                        "total_collected": float(total_collected),
                        "total_settled": float(total_settled),
                        "remaining_amount": float(remaining)
                    }
                }
            
            # Create or get vendor's fund account in Razorpay
            # Get or create contact for vendor
            contact = self._get_or_create_razorpay_contact(vendor)
            
            # Create fund account for vendor
            fund_account = self._create_razorpay_fund_account(
                contact['id'],
                settlement_upi
            )
            
            # Create payout using OWNER's account number
            razorpay_payout = self.client.payout.create({
                'account_number': settings.RAZORPAY_ACCOUNT_NUMBER,  # OWNER's account
                'fund_account_id': fund_account['id'],
                'amount': int(settlement_amount * 100),  # Convert to paise
                'currency': 'INR',
                'mode': 'UPI',
                'purpose': 'settlement',
                'queue_if_low_balance': True,
                'reference_id': f"settlement_event_{event_id}_vendor_{vendor_id}",
                'notes': {
                    'event_id': event_id,
                    'vendor_id': vendor_id,
                    'vendor_name': vendor.full_name,
                    'type': 'event_settlement'
                }
            })
            
            # Create settlement record
            settlement = EventSettlement.objects.create(
                event=event,
                vendor=vendor,
                settled_by=event.created_by,  # Vendor requested
                amount=settlement_amount,
                description=f"Settlement requested to {settlement_upi}",
                status='completed'
            )
            
            logger.info(f"Settlement initiated: {razorpay_payout['id']} for vendor {vendor_id}")
            
            return {
                "IsSuccess": True,
                "Message": "Settlement initiated successfully",
                "Data": {
                    "settlement_id": settlement.id,
                    "razorpay_payout_id": razorpay_payout['id'],
                    "amount": float(settlement_amount),
                    "vendor_upi": settlement_upi,
                    "total_collected": float(total_collected),
                    "total_settled": float(total_settled + settlement_amount),
                    "remaining_amount": float(remaining - settlement_amount)
                }
            }
        
        except Event.DoesNotExist:
            return {
                "IsSuccess": False,
                "Message": "Event not found",
                "Data": None
            }
        except User.DoesNotExist:
            return {
                "IsSuccess": False,
                "Message": "Vendor not found",
                "Data": None
            }
        except Exception as e:
            logger.error(f"Error requesting settlement: {str(e)}")
            return {
                "IsSuccess": False,
                "Message": f"Error: {str(e)}",
                "Data": None
            }
    
    def get_event_settlement_summary(self, event_id):
        """Get settlement summary for event"""
        try:
            from payments.models import EventSettlement
            
            total_collected = EventCollectionTransaction.objects.filter(
                event_id=event_id,
                status='completed'
            ).aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
            
            total_settled = EventSettlement.objects.filter(
                event_id=event_id,
                status='completed'
            ).aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
            
            remaining = total_collected - total_settled
            
            settlements = EventSettlement.objects.filter(
                event_id=event_id,
                status='completed'
            ).order_by('-settlement_date')
            
            settlement_data = [
                {
                    'id': s.id,
                    'vendor': s.vendor.full_name,
                    'amount': float(s.amount),
                    'description': s.description,
                    'date': s.settlement_date.isoformat()
                }
                for s in settlements
            ]
            
            return {
                "IsSuccess": True,
                "Message": "Settlement summary retrieved",
                "Data": {
                    "total_collected": float(total_collected),
                    "total_settled": float(total_settled),
                    "remaining_amount": float(remaining),
                    "settlements": settlement_data
                }
            }
        except Exception as e:
            logger.error(f"Error getting settlement summary: {str(e)}")
            return {
                "IsSuccess": False,
                "Message": f"Error: {str(e)}",
                "Data": None
            }