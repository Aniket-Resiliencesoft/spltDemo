from rest_framework.response import Response
from rest_framework import status

from accounts.models import Role
from accounts.serializer import (
    RoleGetSerializer,
    RoleCreateSerializer,
    RoleUpdateSerializer
)

from common.api.base_api import BaseAuthenticatedAPI
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
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Step 3: Create role
        role = Role.objects.create(
            name=serializer.validated_data['name'],
            is_active=True
        )

        return Response(
            {"message": "Role created successfully", "role_id": role.id},
            status=status.HTTP_201_CREATED
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

        return Response(serializer.data, status=status.HTTP_200_OK)

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
            return Response(
                {"message": "Role not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RoleGetSerializer(role)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            return Response(
                {"message": "Role not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Step 3: Validate update data
        serializer = RoleUpdateSerializer(role, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(
            {"message": "Role updated successfully"},
            status=status.HTTP_200_OK
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
            return Response(
                {"message": "Role not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Step 3: Soft delete
        role.is_active = False
        role.save()

        return Response(
            {"message": "Role deleted successfully"},
            status=status.HTTP_200_OK
        )
