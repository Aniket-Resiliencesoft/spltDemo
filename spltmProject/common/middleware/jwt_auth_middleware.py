from django.http import JsonResponse
from common.utils.jwt_utils import decode_jwt_token

EXEMPT_URLS = (
    '/api/auth/login/',
    '/api/users/register/',
)

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        path = request.path

        # ✅ 1. If NOT an API request → skip JWT
        if not path.startswith('/api/'):
            return self.get_response(request)

        # ✅ 2. Allow public API URLs WITHOUT JWT
        if path.startswith(EXEMPT_URLS):
            return self.get_response(request)

        # ✅ 3. JWT REQUIRED for all other /api/ URLs
        token = None

        # 🔹 Try Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.strip().split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
            else:
                return JsonResponse(
                    {"message": "Invalid Authorization header format. Use: Bearer <token>"},
                    status=401
                )

        # 🔹 Fallback to cookie
        if not token:
            token = request.COOKIES.get('access_token')

        # ❌ Token is mandatory for protected APIs
        if not token:
            return JsonResponse(
                {"message": "Authentication credentials were not provided"},
                status=401
            )

        # 🔹 Validate token
        try:
            payload = decode_jwt_token(token)
            request.jwt_user = payload
        except Exception as ex:
            return JsonResponse(
                {"message": "Invalid or expired token", "detail": str(ex)},
                status=401
            )

        return self.get_response(request)
