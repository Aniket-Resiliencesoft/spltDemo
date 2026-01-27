"""
Dashboard API Views
Endpoints for fetching dashboard statistics and metrics
"""

from rest_framework import status
from django.db.models import Sum, Count
from decimal import Decimal

from common.api.base_api import BaseAuthenticatedAPI
from accounts.models import User
from events.models import Event
from payments.models import EventCollectionTransaction


class DashboardStatsAPI(BaseAuthenticatedAPI):
    """
    GET: Retrieve dashboard statistics
    Returns:
    - total_users: Total active users in system
    - active_events: Total active events
    - total_payment: Total amount collected in payments
    """

    def get(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error

        try:
            # Get total active users
            total_users = User.objects.filter(is_active=True).count()

            # Get total active events
            active_events = Event.objects.filter(
                is_active=True,
                status__in=['active', 'draft']  # Active and draft events
            ).count()

            # Get total payment (sum of completed transactions)
            total_payment = EventCollectionTransaction.objects.filter(
                is_active=True,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            # Get pending payment
            pending_payment = EventCollectionTransaction.objects.filter(
                is_active=True,
                status='pending'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            stats = {
                'total_users': total_users,
                'active_events': active_events,
                'total_payment': float(total_payment),
                'pending_payment': float(pending_payment),
            }

            return self.success_response(
                data=stats,
                message="Dashboard statistics retrieved successfully"
            )

        except Exception as e:
            return self.error_response(
                message=f"Error retrieving dashboard stats: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
