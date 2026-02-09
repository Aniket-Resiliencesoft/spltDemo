from rest_framework import serializers
from accounts.models import User, Role, UserRole


class UserGetSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'email',
            'contact_no',
            'status',
            'is_active',
            'created_at',
            'updated_at',
            'role',
            'profile_image_url',
        ]

    def get_role(self, obj):
        user_role = obj.userrole_set.filter(
            is_active=True
        ).select_related('role').first()

        if user_role:
            return {
                "id": user_role.role.id,
                "name": user_role.role.name
            }

        return None

    def get_profile_image_url(self, obj):
        """Return profile image URL if image exists, otherwise None"""
        if obj.profile_image:
            return obj.profile_image.url
        return None
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'full_name',
            'email',
            'contact_no',
            'password',
        ]
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'full_name',
            'contact_no',
            'status',
        ]

class UserDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_active']

class RoleGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = [
            'id',
            'name',
            'is_active',
            'created_at',
        ]

class RoleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['name']

class RoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['name', 'is_active']

class UserRoleGetSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = UserRole
        fields = [
            'id',
            'user',
            'user_name',
            'role',
            'role_name',
            'is_active',
            'created_at',
        ]

class UserRoleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['user', 'role']


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['is_active']

class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Accepts email and password from client.
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        trim_whitespace=False
    )
    appKey = serializers.IntegerField(required=False, default=0)


class OTPGenerateSerializer(serializers.Serializer):
    """
    Serializer for OTP generation.
    Accepts email and password to generate OTP.
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        trim_whitespace=False
    )


class OTPVerifySerializer(serializers.Serializer):
    """
    Serializer for OTP verification.
    Accepts user_id and OTP to verify and generate JWT token.
    """

    user_id = serializers.IntegerField(required=True)
    otp = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6
    )

class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)
