from django.db import models
from common.models import BaseModel
from accounts.models import User


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
        ('draft', 'Draft'),
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
