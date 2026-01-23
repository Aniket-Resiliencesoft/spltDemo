import jwt
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User, UserRole
from accounts.serializer import LoginSerializer, OTPGenerateSerializer, OTPVerifySerializer
from common.utils.email_service import send_otp_email


class LoginAPI(APIView):
    """
    POST:
    Authenticates user credentials.
    - For ADMIN users: Returns JWT token directly
    - For non-ADMIN users: Generates OTP and returns user_id
    """

    def post(self, request):
        # Step 1: Validate input
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        appKey = int(serializer.validated_data.get('appKey', 0))

        # Step 2: Check if user exists and is active
        try:
            user = User.objects.get(
                email=email,
                is_active=True,
                status=1
            )
        except User.DoesNotExist:
            return Response(
                {"message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Step 3: Verify password
        if not check_password(password, user.password_hash):
            return Response(
                {"message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Step 4: Get user role
        user_role = (
            UserRole.objects
            .select_related('role')
            .filter(user=user, is_active=True)
            .first()
        )

        role_name = user_role.role.name if user_role else 'User'

        # Step 5: Check if user is ADMIN
        is_admin = role_name.upper() == 'ADMIN'

        # Step 6: Admin check - return JWT directly for admin
        if appKey == 1:
            # Admin login only
            if not is_admin:
                return Response(
                    {"message": "Admin access required"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Create JWT payload for admin
            payload = {
                "user_id": user.id,
                "username": user.email,
                "role": role_name,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(
                    minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
                ),
            }

            # Generate JWT token
            token = jwt.encode(
                payload,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )

            return Response(
                {
                    "access_token": token,
                    "token_type": "Bearer",
                    "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    "user": {
                        "id": user.id,
                        "full_name": user.full_name,
                        "email": user.email,
                        "role": role_name
                    }
                },
                status=status.HTTP_200_OK
            )

        # Step 7: For non-admin users, generate OTP
        if is_admin:
            # Admin can login directly
            payload = {
                "user_id": user.id,
                "username": user.email,
                "role": role_name,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(
                    minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
                ),
            }

            token = jwt.encode(
                payload,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )

            return Response(
                {
                    "access_token": token,
                    "token_type": "Bearer",
                    "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    "user": {
                        "id": user.id,
                        "full_name": user.full_name,
                        "email": user.email,
                        "role": role_name
                    }
                },
                status=status.HTTP_200_OK
            )
        else:
            # Non-admin: Generate OTP
            otp = user.generate_otp()
            
            # Send OTP to user's email
            email_result = send_otp_email(
                email=user.email,
                otp=otp,
                user_name=user.full_name
            )
            
            # In production, return only user_id and email (not OTP)
            # The OTP is sent via email
            return Response(
                {
                    "message": "OTP sent to your email. Please verify with the OTP.",
                    "user_id": user.id,
                    "email": user.email,
                    "otp_generated": True,
                    "email_status": email_result.get('status', 'unknown'),
                    "email_message": email_result.get('message', '')
                },
                status=status.HTTP_200_OK
            )

class OTPGenerateAPI(APIView):
    """
    POST:
    Generate OTP for non-admin user login.
    Accepts email and password, generates OTP if credentials are valid.
    """

    def post(self, request):
        print( "OTP Generation Request Data:", request.data )  # Debugging line
        serializer = OTPGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Check if user exists and is active
        try:
            user = User.objects.get(
                email=email,
                is_active=True,
                status=1
            )
        except User.DoesNotExist:
            return Response(
                {"message": "Invalid email or password"},
                status=status.is_client_error
            )

        # Verify password
        if not check_password(password, user.password_hash):
            return Response(
                {"message": "Invalid email or password"},
                status=status.is_client_error
            )

        # Get user role to check if non-admin
        user_role = (
            UserRole.objects
            .select_related('role')
            .filter(user=user, is_active=True)
            .first()
        )

        role_name = user_role.role.name if user_role else 'User'

        if role_name.upper() == 'ADMIN':
            return Response(
                {"message": "Admin users should use direct login"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate OTP
        otp = user.generate_otp()

        # Send OTP to user's email
        email_result = send_otp_email(
            email=user.email,
            otp=otp,
            user_name=user.full_name
        )

        # Return response
        return Response(
            {
                "message": "OTP sent successfully to your email",
                "user_id": user.id,
                "email": user.email,
                "email_status": email_result.get('status', 'unknown'),
                "email_message": email_result.get('message', '')
            },
            status=status.HTTP_200_OK
        )

class OTPVerifyAPI(APIView):
    """
    POST:
    Verify OTP for non-admin user login.
    Accepts user_id and OTP, returns JWT token if OTP is valid.
    """

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        user_id = serializer.validated_data['user_id']
        otp = serializer.validated_data['otp']

        # Get user
        try:
            user = User.objects.get(id=user_id, is_active=True, status=1)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify OTP
        if not user.verify_otp(otp):
            return Response(
                {"message": "Invalid or expired OTP"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Get user role
        user_role = (
            UserRole.objects
            .select_related('role')
            .filter(user=user, is_active=True)
            .first()
        )

        role_name = user_role.role.name if user_role else 'User'

        # Create JWT payload
        payload = {
            "user_id": user.id,
            "username": user.email,
            "role": role_name,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            ),
        }

        # Generate JWT token
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        # Update last login
        user.last_login = datetime.utcnow()
        user.save()

        return Response(
            {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": role_name
                }
            },
            status=status.HTTP_200_OK
        )

