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
