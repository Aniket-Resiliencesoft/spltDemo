from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth.hashers import make_password
from django.db.models import Q

from accounts.models import Role, User, UserRole
from accounts.serializer import (
    UserGetSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserDeleteSerializer
)
from common.api.base_api import BaseAuthenticatedAPI
from accounts.serializer import UserRoleCreateSerializer

class UserListAPI(BaseAuthenticatedAPI):
    """
    GET:
    Returns list of all active users with optional filtering and search.
    Supports search filter on name and email.
    Used in Admin User Management screen.
    """

    def get(self, request):

        error = self.require_admin_role(request)
        if error:
            return error
        
        page_no = int(request.query_params.get('pageNo', 1))
        page_size = int(request.query_params.get('pageSize', 10))
        search_filter = request.query_params.get('search', '').strip()

        qs = User.objects.filter(is_active=True).order_by('-created_at')
        
        # Apply search filter
        if search_filter:
            qs = qs.filter(
                Q(full_name__icontains=search_filter) | 
                Q(email__icontains=search_filter)
            )
        
        # Get total count before pagination
        total_count = qs.count()
        
        offset = (page_no - 1) * page_size
        users = qs[offset:offset + page_size]

        serializer = UserGetSerializer(users, many=True)
        return self.paginated_response(
            data=serializer.data,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
            message="Users retrieved successfully"
        )
    
class UserDetailAPI(APIView):
    """
    GET:
    Returns single user details by user ID.
    Used for View / Edit user screen.
    """

    def get(self, request, user_id):
        try:
            # Fetch user by ID
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserGetSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserCreateAPI(APIView):
    """
    POST:
    Creates a new user.
    Password is hashed before saving.
    """

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            # Create user with hashed password
            user = User.objects.create(
                full_name=data['full_name'],
                email=data['email'],
                contact_no=data['contact_no'],
                password_hash=make_password(data['password']),
                status=1,
                is_active=True
            )

            return Response(
                {"message": "User created successfully", "user_id": user.id},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserUpdateAPI(APIView):
    """
    PUT:
    Updates user basic details.
    """

    def put(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserUpdateSerializer(user, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDeleteAPI(APIView):
    """
    PATCH:
    Soft deletes a user by setting is_active = False.
    No data is permanently removed.
    """

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Soft delete
        user.is_active = False
        user.save()

        return Response(
            {"message": "User deleted successfully"},
            status=status.HTTP_200_OK
        )


class AssignUserRoleAPI(BaseAuthenticatedAPI):
    """
    POST:
    Assigns a role to a user.
    Only one active role per user is allowed.
    Admin access required.
    """

    def post(self, request):
        # Step 1: Ensure admin access
        error = self.require_admin_role(request)
        if error:
            return error

        # Step 2: Validate input (user_id, role_id)
        serializer = UserRoleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data['user'].id
        role_id = serializer.validated_data['role'].id

        # Step 3: Validate user existence
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Step 4: Validate role existence
        try:
            role = Role.objects.get(id=role_id, is_active=True)
        except Role.DoesNotExist:
            return Response(
                {"message": "Role not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Step 5: Deactivate existing roles for user
        UserRole.objects.filter(
            user=user,
            is_active=True
        ).update(is_active=False)

        # Step 6: Assign new role
        UserRole.objects.create(
            user=user,
            role=role,
            is_active=True
        )

        return Response(
            {"message": "Role assigned to user successfully"},
            status=status.HTTP_200_OK
        )
