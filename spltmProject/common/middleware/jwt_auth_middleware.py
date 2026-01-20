from django.http import JsonResponse
from common.utils.jwt_utils import decode_jwt_token


class JWTAuthenticationMiddleware:
    """
    Middleware to authenticate requests using JWT token
    from Authorization header OR cookies.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        token = None

        # ✅ 1. Try Authorization header (Mobile / API clients)
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
            else:
                return JsonResponse(
                    {"message": "Invalid Authorization header format"},
                    status=401
                )

        # ✅ 2. If no header, try Cookie (Desktop / Browser)
        if not token:
            token = request.COOKIES.get('access_token')

        # ✅ 3. If token found, validate it
        if token:
            try:
                payload = decode_jwt_token(token)
                request.jwt_user = payload
            except ValueError as ex:
                return JsonResponse(
                    {"message": str(ex)},
                    status=401
                )

        # ✅ 4. Continue request
        return self.get_response(request)
