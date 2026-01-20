from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class BaseAuthenticatedAPI(APIView):
    """
    Base API class that provides common authentication
    and authorization helper methods.
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

        if request.jwt_user.get('role') != 'ADMIN':
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
