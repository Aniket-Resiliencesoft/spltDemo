import jwt
from datetime import datetime, timedelta

from django.conf import settings
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

def generate_jwt_token(payload: dict) -> str:
    """
    Generates a JWT token with expiry.
    Used during login.
    """

    # Add issued-at and expiry claims
    payload['iat'] = datetime.utcnow()
    payload['exp'] = datetime.utcnow() + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Encode token
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return token

def decode_jwt_token(token: str) -> dict:
    """
    Decodes and validates a JWT token.
    Returns payload if valid.
    Raises exception if invalid or expired.
    """

    try:
        decoded_payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return decoded_payload

    except ExpiredSignatureError:
        raise ValueError("Token has expired")

    except InvalidTokenError:
        raise ValueError("Invalid token")
