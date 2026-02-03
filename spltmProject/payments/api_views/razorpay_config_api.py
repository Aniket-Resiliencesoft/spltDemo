from django.conf import settings
from rest_framework import status

from common.api.base_api import BaseAuthenticatedAPI


class RazorpayConfigAPI(BaseAuthenticatedAPI):
    """GET: Return selected Razorpay config values to authenticated users only."""

    def get(self, request):
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error

        data = {
            'RAZORPAY_KEY_ID': getattr(settings, 'RAZORPAY_KEY_ID', None),
            'RAZORPAY_KEY_SECRET': getattr(settings, 'RAZORPAY_KEY_SECRET', None),
            'RAZORPAY_ACCOUNT_NUMBER': getattr(settings, 'RAZORPAY_ACCOUNT_NUMBER', None),
            'RAZORPAY_WEBHOOK_SECRET': getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None),
        }

        return self.success_response(
            data=data,
            message='Razorpay configuration retrieved successfully',
            status_code=status.HTTP_200_OK
        )
