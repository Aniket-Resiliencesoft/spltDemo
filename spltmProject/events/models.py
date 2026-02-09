from django.db import models
from django.db.models import Sum
from common.models import BaseModel
from accounts.models import User
from decimal import Decimal
from django.db.models import Sum, Case, When, Value, CharField


class Event(BaseModel):
    """
    Event model for managing shared expenses events.
    
    Status:
        - Draft: Event created but not yet active
        - Active: Event is ongoing, expenses can be added
        - Closed: Event is complete, no more expenses
        - Completed: All payments settled
        - Cancelled: Event was cancelled
    """
    
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic fields
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=200, help_text="Any category (e.g., Turf booking, Restaurant, Trip, Party, etc.)")
    description = models.TextField(blank=True, null=True)
    
    # Date & Time fields
    event_date = models.DateField()
    start_date_time = models.DateTimeField()
    end_date_time = models.DateTimeField()
    due_pay_date_time = models.DateTimeField(null=True, blank=True)
    due_pay_before_event_start = models.BooleanField(
        default=True,
        help_text="If True, due_pay_date_time must be before event start. If False, it can be after event start."
    )
    event_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Location fields
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    location=models.TextField(blank=True, null=True)
    custom_category = models.CharField(max_length=100, blank=True, null=True)
    vendor_name=models.CharField(max_length=150,blank=True,null=True)
    # Event details
    persons_count = models.IntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Foreign key to track event creator
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_events'
    )
    
    class Meta:
        db_table = "events"
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['status', 'event_date']),
            models.Index(fields=['created_by', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.category}"

    

    def get_summary(self):
        try:
            from payments.models import EventCollectionTransaction
        except Exception:
            EventCollectionTransaction = None

        collected = Decimal('0.00')
        members = []

        if EventCollectionTransaction:
            qs = EventCollectionTransaction.objects.filter(
                event=self,
                is_active=True
            )

            # ✅ Total collected amount (ONLY completed)
            collected = qs.filter(status='completed').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')

            # ✅ Per-user aggregation
            user_rows = qs.values('user').annotate(
                completed_amount=Sum(
                    'amount',
                    filter=models.Q(status='completed')
                ),
                pending_amount=Sum(
                    'amount',
                    filter=models.Q(status='pending')
                ),
                failed_amount=Sum(
                    'amount',
                    filter=models.Q(status='failed')
                ),
            )


            users = User.objects.in_bulk([row['user'] for row in user_rows])

            for row in user_rows:
                user = users.get(row['user'])

                completed_amount = row['completed_amount'] or Decimal('0.00')
                pending_amount = row['pending_amount'] or Decimal('0.00')
                failed_amount = row['failed_amount'] or Decimal('0.00')

                if completed_amount > 0:
                    payment_status = 'completed'
                    display_amount = completed_amount
                elif pending_amount > 0:
                    payment_status = 'pending'
                    display_amount = pending_amount
                elif failed_amount > 0:
                    payment_status = 'failed'
                    display_amount = failed_amount
                else:
                    payment_status = 'pending'
                    display_amount = Decimal('0.00')

                members.append({
                    'id': user.id,
                    'full_name': getattr(user, 'full_name', str(user)),
                    'email': getattr(user, 'email', None),
                    'paid_amount': display_amount,
                    'payment_status': payment_status,
                })

        created_by_info = None
        if self.created_by:
            cb = self.created_by
            created_by_info = {
                'id': cb.id,
                'full_name': getattr(cb, 'full_name', str(cb)),
                'email': getattr(cb, 'email', None),
            }

        # ===== Vendor payouts info =====
        try:
            from payments.models import VendorPaymentTransaction
        except Exception:
            VendorPaymentTransaction = None

        payouts_list = []
        payouts_summary = {
            'total_requested': Decimal('0.00'),
            'total_processing': Decimal('0.00'),
            'total_completed': Decimal('0.00'),
            'total_failed': Decimal('0.00'),
        }

        if VendorPaymentTransaction:
            pq = VendorPaymentTransaction.objects.filter(event=self.id, is_active=True)
            payouts_summary['total_requested'] = pq.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            payouts_summary['total_processing'] = pq.filter(status='processing').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            payouts_summary['total_completed'] = pq.filter(status='processed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            payouts_summary['total_failed'] = pq.filter(status='failed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            for p in pq.order_by('-created_at'):
                payouts_list.append({
                    'id': p.id,
                    'vendor_name': p.vendor_name,
                    'vendor_upi': p.vendor_upi,
                    'amount': p.amount,
                    'purpose': p.purpose,
                    'status': p.status,
                    'failure_reason': p.failure_reason,
                    'razorpay_payout_id': p.razorpay_payout_id,
                    'created_at': p.created_at,
                    'updated_at': p.updated_at,
                })

        return {
            'members': members,
            'due_date': self.due_pay_date_time,
            'collected_amount': collected,
            'total_amount': self.event_amount,
            'created_by': created_by_info,
            'event_date': self.event_date,
            'start_date_time': self.start_date_time,
            'end_date_time': self.end_date_time,
            'vendor_payouts_summary': payouts_summary,
            'vendor_payouts': payouts_list,
        }
