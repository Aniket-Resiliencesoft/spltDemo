from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from common.models import BaseModel
from events.models import Event
from accounts.models import User



class EventCollectionTransaction(BaseModel):
    """
    Model to track payments/collections for event expenses.
    
    Records transactions when users contribute money to an event.
    Examples:
        - User pays $50 towards trip expenses
        - User settles their share of restaurant bill
        - User contributes to event fund
    """
    
    TRANSACTION_TYPE_CHOICES = [
        ('contribution', 'Contribution'),
        ('refund', 'Refund'),
        ('settlement', 'Settlement'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Foreign Keys
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_transactions'
    )
    
    # Transaction details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default='contribution'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    description = models.TextField(blank=True, null=True)
    
    # Payment method (optional)
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="e.g., Cash, Card, UPI, Bank Transfer"
    )
    
    # Razorpay order ID (optional)
    razorpay_order_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Razorpay order ID for this transaction"
    )
    
    # Razorpay payment ID (optional)
    razorpay_payment_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Razorpay payment ID for this transaction"
    )
    
    # Transaction timestamp
    transaction_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "event_collection_transactions"
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['event', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.amount} ({self.event.title})"


class UserWallet(BaseModel):
    """
    Virtual wallet for each user.
    Stores current balance only.
    Never holds real money - all transactions go through Razorpay.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    
    # Virtual balance (database ledger only)
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Metadata
    razorpay_customer_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Razorpay customer ID for this user"
    )
    
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last synced with Razorpay"
    )
    
    class Meta:
        db_table = "user_wallets"
    
    def __str__(self):
        return f"{self.user.full_name} - Balance: ₹{self.balance}"


class WalletLedger(BaseModel):
    """
    Audit trail for all wallet transactions.
    MANDATORY: Every wallet change creates a ledger entry.
    Maintains compliance and provides full transaction history.
    """
    
    TRANSACTION_TYPE_CHOICES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ]
    
    REASON_CHOICES = [
        ('PAYMENT_RECEIVED', 'Payment Received from Participant'),
        ('PAYOUT_INITIATED', 'Payout to Vendor Initiated'),
        ('PAYOUT_SUCCESS', 'Payout Success'),
        ('PAYOUT_FAILED', 'Payout Failed - Refund'),
        ('EVENT_REFUND', 'Event Cancelled - Refund'),
        ('MANUAL_ADJUSTMENT', 'Manual Adjustment by Admin'),
        ('REVERSAL', 'Transaction Reversal'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wallet_ledger'
    )
    
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES
    )
    
    # Reference IDs for tracking
    event_id = models.IntegerField(null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=50, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=50, null=True, blank=True)
    razorpay_payout_id = models.CharField(max_length=50, null=True, blank=True)
    razorpay_refund_id = models.CharField(max_length=50, null=True, blank=True)
    
    # Balance tracking
    balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Description for audit trail
    description = models.TextField(blank=True)
    
    # Idempotency key to prevent duplicate processing
    idempotency_key = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique key for idempotent operations"
    )
    
    class Meta:
        db_table = "wallet_ledgers"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['razorpay_payment_id']),
            models.Index(fields=['razorpay_payout_id']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.transaction_type} ₹{self.amount}"


class RazorpayOrder(BaseModel):
    """
    Maps Razorpay orders to SplitMoney events.
    Tracks payment state for each participant joining an event.
    """
    
    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('ATTEMPTED', 'Attempted'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    # Event and participant info
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='razorpay_orders'
    )
    
    participant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='razorpay_orders',
        help_text="User joining the event"
    )
    
    # Razorpay identifiers
    razorpay_order_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Order ID from Razorpay"
    )
    
    razorpay_payment_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True,
        help_text="Payment ID after successful payment"
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    currency = models.CharField(max_length=5, default='INR')
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='CREATED'
    )
    
    # Webhook received indicator
    webhook_received = models.BooleanField(
        default=False,
        help_text="Whether payment webhook was received"
    )
    
    webhook_verified = models.BooleanField(
        default=False,
        help_text="Whether payment webhook was verified"
    )
    
    # Additional fields
    receipt = models.CharField(max_length=100, null=True, blank=True)
    notes = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = "razorpay_orders"
        ordering = ['-created_at']
        unique_together = ('event', 'participant')
        indexes = [
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['razorpay_payment_id']),
            models.Index(fields=['event', 'participant']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Order {self.razorpay_order_id} - {self.participant.full_name}"


class RazorpayPayout(BaseModel):
    """
    Tracks vendor payouts after event completion.
    Event creator receives settlement via Razorpay Payout API.
    """
    
    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('PROCESSED', 'Processed'),
        ('FAILED', 'Failed'),
        ('REVERSED', 'Reversed'),
    ]
    
    SETTLEMENT_TYPE_CHOICES = [
        ('UPI', 'UPI'),
        ('BANK', 'Bank Transfer'),
        ('CARD', 'Card'),
    ]
    
    # Event and creator info
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='razorpay_payouts'
    )
    
    vendor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='razorpay_payouts',
        help_text="Event creator (vendor)"
    )
    
    # Razorpay payout identifiers
    razorpay_payout_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Payout ID from Razorpay"
    )
    
    razorpay_contact_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Contact ID for vendor in Razorpay"
    )
    
    razorpay_fund_account_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Fund account ID in Razorpay"
    )
    
    # Payout details
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    currency = models.CharField(max_length=5, default='INR')
    
    # Settlement account info
    settlement_type = models.CharField(
        max_length=20,
        choices=SETTLEMENT_TYPE_CHOICES,
        default='UPI'
    )
    
    settlement_upi = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="UPI ID for payout"
    )
    
    settlement_bank_account = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Bank account number"
    )
    
    settlement_ifsc = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="IFSC code for bank transfer"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='INITIATED'
    )
    
    # Webhook tracking
    webhook_received = models.BooleanField(default=False)
    webhook_verified = models.BooleanField(default=False)
    
    # Additional info
    failure_reason = models.TextField(null=True, blank=True)
    notes = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = "razorpay_payouts"
        ordering = ['-created_at']
        unique_together = ('event', 'vendor')
        indexes = [
            models.Index(fields=['razorpay_payout_id']),
            models.Index(fields=['event']),
            models.Index(fields=['vendor']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Payout {self.razorpay_payout_id} - {self.vendor.full_name}"


class WebhookLog(BaseModel):
    """
    Logs all Razorpay webhooks for debugging and audit.
    Essential for troubleshooting webhook issues.
    """
    
    EVENT_TYPES = [
        ('payment.captured', 'Payment Captured'),
        ('payment.failed', 'Payment Failed'),
        ('payment.authorized', 'Payment Authorized'),
        ('payout.processed', 'Payout Processed'),
        ('payout.failed', 'Payout Failed'),
        ('payout.reversed', 'Payout Reversed'),
    ]
    
    webhook_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique webhook ID from Razorpay"
    )
    
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES
    )
    
    payload = models.JSONField(
        help_text="Full webhook payload from Razorpay"
    )
    
    signature = models.CharField(
        max_length=255,
        help_text="Signature for verification"
    )
    
    signature_verified = models.BooleanField(
        default=False,
        help_text="Whether signature was verified"
    )
    
    processed = models.BooleanField(
        default=False,
        help_text="Whether webhook was processed"
    )
    
    processing_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="SUCCESS or error message"
    )
    
    error_message = models.TextField(null=True, blank=True)
    
    # Reference IDs
    razorpay_entity_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Entity ID from webhook"
    )
    
    class Meta:
        db_table = "webhook_logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['webhook_id']),
            models.Index(fields=['event_type']),
            models.Index(fields=['processed']),
            models.Index(fields=['razorpay_entity_id']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.webhook_id}"

class EventSettlement(BaseModel):
    """
    Track settlement payments from owner to vendor.
    Owner distributes collected money (from EventCollectionTransaction) to vendors.
    
    Money flow:
    - Users pay to join event → goes to OWNER account
    - Owner distributes from collected amount → goes to VENDOR (event creator)
    - Validation: amount_paid_to_vendor <= total_collected
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Event and people involved
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='settlements'
    )
    
    vendor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_settlements',
        help_text="Event creator receiving payment"
    )
    
    settled_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='initiated_settlements',
        help_text="Owner/Admin who initiated settlement"
    )
    
    # Settlement amount
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Description
    description = models.TextField(
        blank=True,
        null=True,
        help_text="e.g., Accommodation, Transport, etc."
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Settlement tracking
    settlement_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "event_settlements"
        ordering = ['-settlement_date']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['vendor']),
            models.Index(fields=['settled_by']),
        ]
    
    def __str__(self):
        return f"Settlement {self.id} - {self.vendor.full_name} - ₹{self.amount}"
    



class VendorPaymentTransaction(models.Model):
    STATUS_CHOICES = (
        ('initiated', 'Initiated'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    # Event context
    event = models.BigIntegerField()

    # User who initiated the payment
    initiated_by = models.BigIntegerField()

    # Vendor details
    vendor_name = models.CharField(max_length=255)
    vendor_upi = models.CharField(max_length=100)

    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=255, blank=True)

    # Razorpay references
    razorpay_contact_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_fund_account_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_payout_id = models.CharField(max_length=255, null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated'
    )

    # Failure reason (if any)
    failure_reason = models.TextField(blank=True)

    # Meta
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vendor_payment_transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['status']),
            models.Index(fields=['razorpay_payout_id']),
        ]

    def __str__(self):
        return f"{self.event} | {self.vendor_upi} | {self.amount} | {self.status}"
