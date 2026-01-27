from rest_framework.response import Response
from rest_framework import status

from accounts.models import Role
from accounts.serializer import (
    RoleGetSerializer,
    RoleCreateSerializer,
    RoleUpdateSerializer
)

from common.api.base_api import BaseAuthenticatedAPI
from common.responses import api_response_success, api_response_error
class RoleCreateAPI(BaseAuthenticatedAPI):
    """
    POST:
    Creates a new role.
    Admin access required.
    """

    def post(self, request):
        # Step 1: Ensure admin access
        error = self.require_authentication(request)
        if error:
            return error

        # Step 2: Validate input
        serializer = RoleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response_error(
                message="Validation failed",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Step 3: Create role
        role = Role.objects.create(
            name=serializer.validated_data['name'],
            is_active=True
        )

        return api_response_success(
            data={"role_id": role.id},
            message="Role created successfully",
            status_code=status.HTTP_201_CREATED
        )
class RoleListAPI(BaseAuthenticatedAPI):
    """
    GET:
    Returns list of all active roles.
    Admin access required.
    """

    def get(self, request):
        # Step 1: Ensure admin access
        error = self.require_authentication(request)
        if error:
            return error

        # Step 2: Fetch active roles
        roles = Role.objects.filter(is_active=True).order_by('name')

        # Step 3: Serialize data
        serializer = RoleGetSerializer(roles, many=True)

        return api_response_success(data=serializer.data)

class RoleDetailAPI(BaseAuthenticatedAPI):
    """
    GET:
    Returns role details by role ID.
    Admin access required.
    """

    def get(self, request, role_id):
        # Step 1: Ensure admin access
        error = self.require_admin_role(request)
        if error:
            return error

        # Step 2: Fetch role
        try:
            role = Role.objects.get(id=role_id, is_active=True)
        except Role.DoesNotExist:
            return api_response_error(
                message="Role not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = RoleGetSerializer(role)
        return api_response_success(data=serializer.data)

class RoleUpdateAPI(BaseAuthenticatedAPI):
    """
    PUT:
    Updates role name or status.
    Admin access required.
    """

    def put(self, request, role_id):
        # Step 1: Ensure admin access
        error = self.require_admin_role(request)
        if error:
            return error

        # Step 2: Fetch role
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return api_response_error(
                message="Role not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Step 3: Validate update data
        serializer = RoleUpdateSerializer(role, data=request.data)
        if not serializer.is_valid():
            return api_response_error(
                message="Validation failed",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        return api_response_success(
            message="Role updated successfully",
            status_code=status.HTTP_200_OK
        )

class RoleDeleteAPI(BaseAuthenticatedAPI):
    """
    PATCH:
    Soft deletes a role by setting is_active = False.
    Admin access required.
    """

    def patch(self, request, role_id):
        # Step 1: Ensure admin access
        error = self.require_admin_role(request)
        if error:
            return error

        # Step 2: Fetch role
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return api_response_error(
                message="Role not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Step 3: Soft delete
        role.is_active = False
        role.save()

        return api_response_success(
            message="Role deleted successfully",
            status_code=status.HTTP_200_OK
        )
