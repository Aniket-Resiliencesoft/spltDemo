from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User
from accounts.serializer import (
    ResetPasswordRequestSerializer,
    ResetPasswordVerifyOTPSerializer
)
from common.utils.email_service import send_otp_email


# ==========================================================
# RESET PASSWORD RESPONSE HELPER
# ==========================================================

def reset_password_response(is_success, message, data=None, status_code=status.HTTP_200_OK):
    return Response(
        {
            "IsSuccess": is_success,
            "Message": message,
            "Data": data
        },
        status=status_code
    )


# ==========================================================
# RESET PASSWORD REQUEST API
# ==========================================================

class ResetPasswordRequestAPI(APIView):
    """
    POST:
    Request password reset by providing email or contact number.
    - Searches for user by email or contact_no
    - Generates and sends OTP to user's email
    - Updates user table with OTP
    
    Request:
    {
        "identifier": "user@example.com" or "9876543210"
    }
    
    Response:
    {
        "IsSuccess": true,
        "Message": "OTP sent to your email",
        "Data": {
            "user_id": 1,
            "email": "user@example.com",
            "otp_generated": true,
            "email_status": "success",
            "email_message": "Email sent successfully"
        }
    }
    """

    def post(self, request):
        serializer = ResetPasswordRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return reset_password_response(
                False,
                "Invalid input",
                serializer.errors,
                status.HTTP_400_BAD_REQUEST
            )

        identifier = serializer.validated_data.get("identifier")

        # Search for user by email or contact_no
        user = None
        try:
            # Try to find by email first
            if '@' in identifier:
                user = User.objects.get(
                    email=identifier,
                    is_active=True,
                    status=1
                )
            else:
                # Try to find by contact_no
                user = User.objects.get(
                    contact_no=identifier,
                    is_active=True,
                    status=1
                )
        except User.DoesNotExist:
            return reset_password_response(
                False,
                "User not found with the provided email or contact number",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Generate OTP and save to database
        otp = user.generate_otp()

        # Send OTP to user's email
        email_result = send_otp_email(
            email=user.email,
            otp=otp,
            user_name=user.full_name
        )

        # Log email result
        if email_result.get("status") == "error":
            print(f"Reset Password OTP - Failed: {email_result.get('message')}")
        else:
            print(f"Reset Password OTP - Success: {email_result.get('message')}")

        return reset_password_response(
            True,
            "OTP sent to your email. Please verify to reset password.",
            {
                "user_id": user.id,
                "email": user.email,
                "otp_generated": True,
                "email_status": email_result.get("status", "unknown"),
                "email_message": email_result.get("message", "")
            }
        )


# ==========================================================
# RESET PASSWORD VERIFY OTP API
# ==========================================================

class ResetPasswordVerifyOTPAPI(APIView):
    """
    POST:
    Verify OTP and reset password.
    - Validates OTP (must be correct and not expired within 10 minutes)
    - Updates user password
    - Clears the OTP from database
    
    Request:
    {
        "user_id": 1,
        "otp": "123456",
        "new_password": "newPassword123",
        "confirm_password": "newPassword123"
    }
    
    OR
    
    {
        "email": "user@example.com",
        "otp": "123456",
        "new_password": "newPassword123",
        "confirm_password": "newPassword123"
    }
    
    Response:
    {
        "IsSuccess": true,
        "Message": "Password reset successfully",
        "Data": {
            "user_id": 1,
            "email": "user@example.com",
            "message": "Your password has been reset successfully"
        }
    }
    """

    def post(self, request):
        serializer = ResetPasswordVerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return reset_password_response(
                False,
                "Invalid input",
                serializer.errors,
                status.HTTP_400_BAD_REQUEST
            )

        user_id = serializer.validated_data.get("user_id")
        email = serializer.validated_data.get("email")
        otp = serializer.validated_data.get("otp")
        new_password = serializer.validated_data.get("new_password")

        # Find user by user_id or email
        user = None
        try:
            if user_id:
                user = User.objects.get(id=user_id, is_active=True, status=1)
            elif email:
                user = User.objects.get(email=email, is_active=True, status=1)
        except User.DoesNotExist:
            return reset_password_response(
                False,
                "User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Verify OTP
        if not user.verify_otp(otp):
            return reset_password_response(
                False,
                "Invalid or expired OTP. Please request a new OTP.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Update password
        user.password_hash = make_password(new_password)
        user.save(update_fields=["password_hash"])

        return reset_password_response(
            True,
            "Password reset successfully",
            {
                "user_id": user.id,
                "email": user.email,
                "message": "Your password has been reset successfully"
            }
        )
