from django.db import models
from django.db.models import Sum
from common.models import BaseModel
from accounts.models import User
from decimal import Decimal


class Event(BaseModel):
    """
    Event model for managing shared expenses events.
    
    Categories:
        - Turf booking
        - Restaurant bill sharing
        - Trip booking
        - Party / Celebration
        - Custom event
    
    Status:
        - Draft: Event created but not yet active
        - Active: Event is ongoing, expenses can be added
        - Closed: Event is complete, no more expenses
        - Completed: All payments settled
        - Cancelled: Event was cancelled
    """
    
    CATEGORY_CHOICES = [
        ('turf', 'Turf booking'),
        ('restaurant', 'Restaurant bill sharing'),
        ('trip', 'Trip booking'),
        ('party', 'Party / Celebration'),
        ('custom', 'Custom event'),
    ]
    
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic fields
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True)
    
    # Date & Time fields
    event_date = models.DateField()
    start_date_time = models.DateTimeField()
    end_date_time = models.DateTimeField()
    due_pay_date = models.DateField()
    event_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Location fields
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
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
        return f"{self.title} - {self.get_category_display()}"

    def get_summary(self):
        """
        Return event summary including members (derived from event transactions
        as a fallback), collected amount, total amount, due date and creator details.

        Returned dict:
        {
            'members': [{ 'id': ..., 'full_name': ..., 'email': ... }, ...],
            'due_date': date,
            'collected_amount': Decimal,
            'total_amount': Decimal,
            'created_by': { 'id': ..., 'full_name': ..., 'email': ... },
            'event_date': date,
            'start_date_time': datetime,
            'end_date_time': datetime,
        }
        """
        # Lazy import to avoid circular imports
        try:
            from payments.models import EventCollectionTransaction
        except Exception:
            EventCollectionTransaction = None

        collected = Decimal('0.00')
        member_ids = []
        if EventCollectionTransaction is not None:
            qs = EventCollectionTransaction.objects.filter(event=self)
            agg = qs.filter(status='completed').aggregate(total=Sum('amount'))
            if agg and agg.get('total') is not None:
                collected = agg['total']
            member_ids = list(qs.values_list('user', flat=True).distinct())

        members = []
        if member_ids:
            users = User.objects.filter(id__in=member_ids)
            for u in users:
                members.append({
                    'id': u.id,
                    'full_name': getattr(u, 'full_name', str(u)),
                    'email': getattr(u, 'email', None),
                    # 'ammount_paid': qs.filter(user=u, status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
                })

        created_by_info = None
        if self.created_by:
            cb = self.created_by
            created_by_info = {
                'id': cb.id,
                'full_name': getattr(cb, 'full_name', str(cb)),
                'email': getattr(cb, 'email', None),
            }

        return {
            'members': members,
            'due_date': self.due_pay_date,
            'collected_amount': collected,
            'total_amount': self.event_amount,
            'created_by': created_by_info,
            'event_date': self.event_date,
            'start_date_time': self.start_date_time,
            'end_date_time': self.end_date_time,
        }
