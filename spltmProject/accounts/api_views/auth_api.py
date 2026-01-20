import jwt
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User, UserRole
from accounts.serializer import LoginSerializer

class LoginAPI(APIView):
    """
    POST:
    Authenticates user credentials and returns JWT token.
    """

    def post(self, request):
        # Step 1: Validate input using LoginSerializer
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Step 2: Check if user exists and is active
        try:
            user = User.objects.get(email=email, is_active=True, status=1)
        except User.DoesNotExist:
            return Response(
                {"message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Step 3: Verify password hash
        if not check_password(password, user.password_hash):
            return Response(
                {"message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Step 4: Get user role (assuming one active role per user)
        user_role = (
            UserRole.objects
            .select_related('role')
            .filter(user=user, is_active=True)
            .first()
        )

        role_name = user_role.role.name if user_role else None

        # Step 5: Create JWT payload
        payload = {
            "user_id": user.id,
            "username": user.email,
            "role": role_name,
            "exp": datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            ),
            "iat": datetime.utcnow()
        }

        # Step 6: Generate JWT token
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        # Step 7: Return response
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
