import jwt
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User, UserRole
from accounts.serializer import (
    LoginSerializer,
    OTPGenerateSerializer,
    OTPVerifySerializer
)
from common.utils.email_service import send_otp_email
from common.responses import api_response_success, api_response_error


# ==========================================================
# AUTH RESPONSE HELPER (AUTH MODULE ONLY – NO response.py)
# ==========================================================

def auth_response(is_success, message, data=None, status_code=status.HTTP_200_OK):
    return Response(
        {
            "IsSuccess": is_success,
            "Message": message,
            "Data": data
        },
        status=status_code
    )


# ==========================================================
# LOGIN API
# ==========================================================

class LoginAPI(APIView):
    """
    POST:
    - ADMIN: Direct JWT login
    - NON-ADMIN:
        - email_verified = True → Direct JWT login
        - email_verified = False → OTP generation
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return auth_response(
                False,
                "Invalid input data",
                serializer.errors,
                status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        appKey = int(serializer.validated_data.get("appKey", 0))

        # --------------------------------------------------
        # Validate user
        # --------------------------------------------------
        try:
            user = User.objects.get(
                email=email,
                is_active=True,
                status=1
            )
        except User.DoesNotExist:
            return auth_response(
                False,
                "Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        if not check_password(password, user.password_hash):
            return auth_response(
                False,
                "Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # --------------------------------------------------
        # Role check
        # --------------------------------------------------
        user_role = (
            UserRole.objects
            .select_related("role")
            .filter(user=user, is_active=True)
            .first()
        )

        role_name = user_role.role.name if user_role else "User"
        is_admin = role_name.upper() == "ADMIN"

        # --------------------------------------------------
        # Admin-only login (appKey = 1)
        # --------------------------------------------------
        if appKey == 1:
            if not is_admin:
                return auth_response(
                    False,
                    "Admin access required",
                    status_code=status.HTTP_403_FORBIDDEN
                )

            return auth_response(
                True,
                "Login successful",
                self._generate_token(user, role_name)
            )

        # --------------------------------------------------
        # Admin direct login (without OTP)
        # --------------------------------------------------
        if is_admin:
            return auth_response(
                True,
                "Login successful",
                self._generate_token(user, role_name)
            )

        # --------------------------------------------------
        # Non-admin direct login if email already verified
        # --------------------------------------------------
        if user.email_verified:
             return auth_response(
                    True,
                    "Login successful",
                    self._generate_token(user, role_name)
                )

        # --------------------------------------------------
        # Non-admin OTP flow (email NOT verified)
        # --------------------------------------------------
        otp = user.generate_otp()

        email_result = send_otp_email(
            email=user.email,
            otp=otp,
            user_name=user.full_name
        )

        return auth_response(
            True,
            "OTP sent to your email. Please verify.",
            {
                "user_id": user.id,
                "email": user.email,
                "otp_generated": True,
                "email_status": email_result.get("status", "unknown"),
                "email_message": email_result.get("message", "")
            }
        )

    # --------------------------------------------------
    # JWT GENERATOR
    # --------------------------------------------------
    def _generate_token(self, user, role_name):
        payload = {
            "user_id": str(user.id),  # UUID safe
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

        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": role_name
            }
        }
    

# ==========================================================
# OTP GENERATE API
# ==========================================================

class OTPGenerateAPI(APIView):
    """
    POST:
    Generate OTP for NON-ADMIN users
    """

    def post(self, request):
        serializer = OTPGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return auth_response(
                False,
                "Invalid input",
                serializer.errors,
                status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email, is_active=True, status=1)
        except User.DoesNotExist:
            return auth_response(
                False,
                "Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        if not check_password(password, user.password_hash):
            return auth_response(
                False,
                "Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        user_role = (
            UserRole.objects
            .select_related("role")
            .filter(user=user, is_active=True)
            .first()
        )

        if user_role and user_role.role.name.upper() == "ADMIN":
            return auth_response(
                False,
                "Admin users should use direct login",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Check if email is already verified
        if user.email_verified:
            return auth_response(
                False,
                "Email already verified. Please login directly.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        otp = user.generate_otp()

        email_result = send_otp_email(
            email=user.email,
            otp=otp,
            user_name=user.full_name
        )

        # Log if OTP email fails
        if email_result.get("status") == "error":
            print(f"OTP sent - Failed: {email_result.get('message')}")
        else:
            print(f"OTP sent - Success: {email_result.get('message')}")

        return auth_response(
            True,
            "OTP sent successfully",
            {
                "user_id": user.id,
                "email": user.email,
                "email_status": email_result.get("status", "unknown"),
                "email_message": email_result.get("message", "")
            }
        )


# ==========================================================
# OTP VERIFY API
# ==========================================================

class OTPVerifyAPI(APIView):
    """
    POST:
    Verify OTP and return JWT
    """

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return auth_response(
                False,
                "Invalid input",
                serializer.errors,
                status.HTTP_400_BAD_REQUEST
            )

        user_id = serializer.validated_data["user_id"]
        otp = serializer.validated_data["otp"]

        try:
            user = User.objects.get(id=user_id, is_active=True, status=1)
        except User.DoesNotExist:
            return auth_response(
                False,
                "User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if not user.verify_otp(otp):
            return auth_response(
                False,
                "Invalid or expired OTP",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        user_role = (
            UserRole.objects
            .select_related("role")
            .filter(user=user, is_active=True)
            .first()
        )

        role_name = user_role.role.name if user_role else "User"
        token_data = LoginAPI()._generate_token(user, role_name)

        user.last_login = datetime.utcnow()
        user.save(update_fields=["last_login"])

        return auth_response(
            True,
            "OTP verified successfully",
            token_data
        )
