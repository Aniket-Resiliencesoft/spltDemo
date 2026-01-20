from django.urls import path
from accounts.api_views.auth_api import LoginAPI

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
    path('users/', UserListAPI.as_view()),
    path('users/<int:user_id>/', UserDetailAPI.as_view()),
    path('users/create/', UserCreateAPI.as_view()),
    path('users/<int:user_id>/update/', UserUpdateAPI.as_view()),
    path('users/<int:user_id>/delete/', UserDeleteAPI.as_view()),
]

urlpatterns += [
    path('auth/login/', LoginAPI.as_view()),
]

urlpatterns += [
    path('roles/', RoleListAPI.as_view()),
    path('roles/create/', RoleCreateAPI.as_view()),
    path('roles/<int:role_id>/', RoleDetailAPI.as_view()),
    path('roles/<int:role_id>/update/', RoleUpdateAPI.as_view()),
    path('roles/<int:role_id>/delete/', RoleDeleteAPI.as_view()),
]

urlpatterns += [
    path('users/assign-role/', AssignUserRoleAPI.as_view()),
]

urlpatterns +=[
    path('login/',ui_views.login_view),
]