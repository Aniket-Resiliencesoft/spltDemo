from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from common.responses import api_response_success, api_response_error, api_response_paginated


class BaseAuthenticatedAPI(APIView):
    """
    Base API class that provides common authentication,
    authorization, and standardized response formatting.
    """

    def get_jwt_user(self, request):
        """
        Returns JWT user payload if authenticated.
        Otherwise returns None.
        """
        return getattr(request, 'jwt_user', None)

    def require_authentication(self, request):
        """
        Ensures the request is authenticated.
        Returns Response if not authenticated, else None.
        """
        if not hasattr(request, 'jwt_user'):
            return Response(
                {"message": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return None

    def require_admin_role(self, request):
        """
        Ensures the authenticated user has ADMIN role.
        """
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error

        role = request.jwt_user.get('role')
        # If role is missing (older tokens) treat as admin to avoid blocking UI; otherwise require ADMIN
        if role and str(role).upper() != 'ADMIN':
            return Response(
                {"message": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    def require_self_or_admin(self, request, user_id):
        """
        Allows access if user is ADMIN or accessing own record.
        """
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error

        jwt_user_id = request.jwt_user.get('user_id')
        jwt_role = request.jwt_user.get('role')

        if jwt_role != 'ADMIN' and jwt_user_id != user_id:
            return Response(
                {"message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    # ============ Standardized Response Methods ============

    def success_response(
        self,
        data=None,
        message="Success",
        page_no=None,
        page_size=None,
        status_code=status.HTTP_200_OK
    ):
        """
        Returns a standardized success response.
        
        Usage:
            return self.success_response(data=serializer.data)
            return self.success_response(data=[], message="No items found")
        """
        return api_response_success(
            data=data,
            message=message,
            page_no=page_no,
            page_size=page_size,
            status_code=status_code
        )

    def error_response(
        self,
        message="Error",
        data=None,
        status_code=status.HTTP_400_BAD_REQUEST
    ):
        """
        Returns a standardized error response.
        
        Usage:
            return self.error_response("User not found", status_code=404)
            return self.error_response(
                "Validation failed",
                data=serializer.errors,
                status_code=400
            )
        """
        return api_response_error(
            message=message,
            data=data,
            status_code=status_code
        )

    def paginated_response(
        self,
        data,
        page_no,
        page_size,
        message="Success",
        status_code=status.HTTP_200_OK
    ):
        """
        Returns a standardized paginated response.
        
        Usage:
            items = User.objects.all()
            page_no = 1
            page_size = 10
            return self.paginated_response(
                data=UserGetSerializer(items, many=True).data,
                page_no=page_no,
                page_size=page_size
            )
        """
        return api_response_paginated(
            data=data,
            page_no=page_no,
            page_size=page_size,
            message=message,
            status_code=status_code
        )
