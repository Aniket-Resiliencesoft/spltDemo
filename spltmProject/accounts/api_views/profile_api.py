from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth.hashers import make_password, check_password

from accounts.models import User, UserRole, Role
from accounts.serializer import (
    UserGetSerializer,
    ProfileRegisterSerializer,
    ProfileUpdateSerializer,
)
from common.responses import api_response_success, api_response_error
from common.api.base_api import BaseAuthenticatedAPI


class ProfileRegisterAPI(APIView):
    """
    POST:
    Registers a new user with profile image.
    Accepts:
        - full_name: str (required)
        - email: str (required, must be unique)
        - contact_no: str (required)
        - password: str (required)
        - profile_image: file (optional)
    Returns:
        - user_id: int
        - email: str
        - full_name: str
    """

    def post(self, request):
        serializer = ProfileRegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data

            # Check if user with this email already exists
            if User.objects.filter(email=data['email']).exists():
                return api_response_error(
                    message="User with this email already exists",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Get profile image from request.FILES if provided, otherwise None
            profile_image = request.FILES.get('profile_image') if 'profile_image' in request.FILES else None

            # Create user with hashed password
            user = User.objects.create(
                full_name=data['full_name'],
                email=data['email'],
                contact_no=data['contact_no'],
                password_hash=make_password(data['password']),
                status=1,
                is_active=True,
                profile_image=profile_image  # Save image only if provided, else remains empty
            )

            return api_response_success(
                data={
                    "user_id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "profile_image": user.profile_image.url if user.profile_image else None,
                },
                message="User registered successfully",
                status_code=status.HTTP_201_CREATED
            )

        return api_response_error(
            message="Validation failed",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ProfileGetByIdAPI(APIView):
    """
    GET:
    Retrieves user profile details by user ID.
    Returns full user information including profile image.
    Path Parameter:
        - user_id: int
    Returns:
        - User object with all profile details
    """

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return api_response_error(
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = UserGetSerializer(user)
        data = serializer.data
        
        # Add profile image URL if exists
        if user.profile_image:
            data['profile_image_url'] = user.profile_image.url
        else:
            data['profile_image_url'] = None

        return api_response_success(
            data=data,
            message="User profile retrieved successfully"
        )


class ProfileUpdateAPI(APIView):

    def put(self, request, user_id):

        print("Received profile update request for user_id:", user_id)

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return api_response_error(
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # IMPORTANT: pass instance
        serializer = ProfileUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            data = serializer.validated_data

            # Update fields
            if 'full_name' in data:
                user.full_name = data['full_name']

            if 'email' in data:
                user.email = data['email']

            if 'contact_no' in data:
                user.contact_no = data['contact_no']

            if 'status' in data:
                user.status = data['status']

            # Password update logic
            if 'password' in data:

                new_password = data['password']
                old_password = request.data.get('old_password')

                if not old_password:
                    return api_response_error(
                        message="Old password is required to change password",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                if not check_password(old_password, user.password_hash):
                    return api_response_error(
                        message="Old password is incorrect",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                if check_password(new_password, user.password_hash):
                    return api_response_error(
                        message="New password cannot be the same as old password",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                user.password_hash = make_password(new_password)

            # Profile image update
            if 'profile_image' in request.FILES:
                if user.profile_image:
                    user.profile_image.delete()
                user.profile_image = request.FILES['profile_image']

            user.save()

            updated_serializer = UserGetSerializer(user)
            response_data = updated_serializer.data

            response_data['profile_image_url'] = (
                user.profile_image.url if user.profile_image else None
            )

            return api_response_success(
                data=response_data,
                message="User profile updated successfully",
                status_code=status.HTTP_200_OK
            )

        return api_response_error(
            message="Validation failed",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
