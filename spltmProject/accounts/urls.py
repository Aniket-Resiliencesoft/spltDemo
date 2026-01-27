from django.urls import path
from accounts.api_views.auth_api import LoginAPI, OTPGenerateAPI, OTPVerifyAPI
from accounts.api_views.dashboard_api import DashboardStatsAPI

from accounts.api_views.user_api import (
    AssignUserRoleAPI,
    UserListAPI,
    UserDetailAPI,
    UserCreateAPI,
    UserUpdateAPI,
    UserDeleteAPI
)
from accounts.api_views.roles_api import (
    RoleCreateAPI,
    RoleListAPI,
    RoleDetailAPI,
    RoleUpdateAPI,
    RoleDeleteAPI
)
from accounts import ui_views

urlpatterns = [
    path('api/users/', UserListAPI.as_view()),
    path('api/users/<int:user_id>/', UserDetailAPI.as_view()),
    path('api/users/create/', UserCreateAPI.as_view()),
    path('api/users/<int:user_id>/update/', UserUpdateAPI.as_view()),
    path('api/users/<int:user_id>/delete/', UserDeleteAPI.as_view()),
]

urlpatterns += [
    path('api/auth/login/', LoginAPI.as_view()),
    path('api/auth/otp/generate/', OTPGenerateAPI.as_view()),
    path('api/auth/otp/verify/', OTPVerifyAPI.as_view()),
]

urlpatterns += [
    path('api/roles/', RoleListAPI.as_view()),
    path('api/roles/create/', RoleCreateAPI.as_view()),
    path('api/roles/<int:role_id>/', RoleDetailAPI.as_view()),
    path('api/roles/<int:role_id>/update/', RoleUpdateAPI.as_view()),
    path('api/roles/<int:role_id>/delete/', RoleDeleteAPI.as_view()),
]

urlpatterns += [
    path('api/users/assign-role/', AssignUserRoleAPI.as_view()),
]

urlpatterns += [
    path('api/dashboard/stats/', DashboardStatsAPI.as_view()),
]

urlpatterns +=[
    path('login/',ui_views.login_view),
    path('register/', ui_views.register_view, name='register'),
    path('verify-otp/', ui_views.verify_otp_view, name='verify_otp'),
    path('dashboard/', ui_views.dashboard_view, name='dashboard'),
    path('api/auth/generateOTP',OTPGenerateAPI.as_view()),
    path('api/auth/verifyOTP',OTPVerifyAPI.as_view()),
    path('logout/', ui_views.logout_view, name='logout'),
    path('stream/dashboard/', ui_views.dashboard_stream, name='dashboard_stream'),
]

# UI pages
urlpatterns += [
    path('users', ui_views.user_list_view, name='users'),
    path('users/create-ui/', ui_views.user_create_view, name='user_create_ui'),
]
