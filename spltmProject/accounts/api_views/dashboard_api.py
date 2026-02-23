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
from events.utils import compute_split
from payments.models import EventCollectionTransaction
from payments.models import EventCollectionTransaction, RazorpayOrder, RazorpayPayout, VendorPaymentTransaction

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
                status__in=['active', 'created']  # Active and draft events
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

            payout_payment = VendorPaymentTransaction.objects.filter(
                    is_active=True,
                    status='PROCESSED'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')


            stats = {
                'total_users': total_users,
                'active_events': active_events,
                'total_payment': float(total_payment),
                'pending_payment': float(pending_payment),
                'pay_Outs' : float(payout_payment),
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


class UserDashboardAPI(BaseAuthenticatedAPI):
    """
    GET: Retrieve authenticated user's dashboard data
    Returns:
    - total_created_events: Count of events created by user
    - total_joined_events: Count of events joined by user
    - total_wallet_balance: Total contributed amount across all events
    """

    def get(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error

        try:
            user_id = request.jwt_user['user_id']
            
            # Get count of events created by user
            total_created_events = Event.objects.filter(
                created_by_id=user_id,
                is_active=True
            ).count()
            
            # Get count of events joined by user (distinct events user has transactions in)
            total_joined_events = EventCollectionTransaction.objects.filter(
                user_id=user_id,
                is_active=True
            ).values('event_id').distinct().count()
            
            # Compute total_wallet_balance as the sum of total_collected_without_admin
            # across all events created by this user (i.e., per_head * participants_count per event).
            total_wallet_balance = Decimal('0')
            try:
                events_qs = Event.objects.filter(created_by_id=user_id, is_active=True).values('id', 'event_amount', 'persons_count')
                for ev in events_qs:
                    try:
                        _sp = compute_split(ev.get('event_amount'), ev.get('persons_count'))
                        per_head = Decimal(str(_sp.get('per_head') or Decimal('0')))
                    except Exception:
                        per_head = Decimal('0')

                    participants_count = EventCollectionTransaction.objects.filter(
                        event_id=ev.get('id'),
                        is_active=True
                    ).values('user_id').distinct().count()

                    total_wallet_balance += (per_head * Decimal(participants_count))
            except Exception:
                total_wallet_balance = Decimal('0')
            
            dashboard_data = {
                'total_created_events': total_created_events,
                'total_joined_events': total_joined_events,
                'total_wallet_balance': float(total_wallet_balance),
            }
            
            return self.success_response(
                data=dashboard_data,
                message="User dashboard data retrieved successfully"
            )

        except Exception as e:
            return self.error_response(
                message=f"Error retrieving user dashboard: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
