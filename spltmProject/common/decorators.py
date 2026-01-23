from functools import wraps
from django.shortcuts import redirect, render
from django.http import HttpResponse
from common.utils.jwt_utils import decode_jwt_token


def login_required_view(view_func):
    """
    Decorator for Django views (HTML pages) that require JWT authentication.
    Redirects to login if token is missing or invalid.
    Redirects to unauthorised.html if token is invalid.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get token from cookie or localStorage (via request header)
        token = request.COOKIES.get('access_token')
        
        if not token:
            # No token found, redirect to login
            return redirect('/')
        
        # Try to decode and validate the token
        try:
            payload = decode_jwt_token(token)
            # Attach user info to request for use in view
            request.jwt_user = payload
            return view_func(request, *args, **kwargs)
        except Exception as ex:
            # Token is invalid or expired, show unauthorised page
            return render(request, 'unauthorised.html', status=401)
    
    return wrapper
