from rest_framework.response import Response
from rest_framework import status

from accounts.models import User
from events.models import Event
from payments.models import EventCollectionTransaction
from common.api.base_api import BaseAuthenticatedAPI


class AdminDashboardStatsAPI(BaseAuthenticatedAPI):
    """
    GET: Return aggregated counts for the admin dashboard.
    - total_users: active users
    - active_events: events with status != cancelled and is_active=True
    - vendors: placeholder (0) as vendor model is not defined yet
    - total_payments: count of completed transactions
    """

    def get(self, request):
        # Admin only
        err = self.require_admin_role(request)
        if err:
            return err

        total_users = User.objects.filter(is_active=True).count()
        active_events = Event.objects.filter(is_active=True).exclude(status='cancelled').count()
        vendors = 0  # vendor model not present in this codebase
        total_payments = EventCollectionTransaction.objects.filter(is_active=True, status='completed').count()

        data = {
            "total_users": total_users,
            "active_events": active_events,
            "vendors": vendors,
            "total_payments": total_payments,
        }

        return Response(data, status=status.HTTP_200_OK)
