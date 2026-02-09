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


# =======================================
# Reset Password Serializers
# =======================================

class ResetPasswordRequestSerializer(serializers.Serializer):
    """
    Serializer for reset password request.
    Accepts: email or contact_no to identify user and generate OTP.
    """
    identifier = serializers.CharField(
        required=True,
        help_text="Email or contact number"
    )


class ResetPasswordVerifyOTPSerializer(serializers.Serializer):
    """
    Serializer for verifying reset password OTP and updating password.
    Accepts: user_id/email, otp, and new_password.
    """
    user_id = serializers.IntegerField(required=False, allow_null=True)
    email = serializers.EmailField(required=False, allow_null=True)
    otp = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=6,
        help_text="New password must be at least 6 characters"
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=6,
        help_text="Confirm password must match new password"
    )

    def validate(self, data):
        """Validate that either user_id or email is provided"""
        if not data.get('user_id') and not data.get('email'):
            raise serializers.ValidationError(
                "Either user_id or email must be provided"
            )
        
        """Validate that new_password and confirm_password match"""
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError(
                "new_password and confirm_password must match"
            )
        
        return data


# =======================================
# Profile APIs Serializers
# =======================================

class ProfileRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with profile image.
    Accepts: full_name, email, contact_no, password, profile_image (optional)
    """
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'full_name',
            'email',
            'contact_no',
            'password',
            'profile_image',
        ]

    def validate_email(self, value):
        """Validate that email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value

    def validate_contact_no(self, value):
        """Validate contact number length"""
        if len(value) < 10:
            raise serializers.ValidationError("Contact number must be at least 10 digits")
        if len(value) > 15:
            raise serializers.ValidationError("Contact number cannot exceed 15 digits")
        return value


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information.
    Accepts: full_name, contact_no, password, profile_image, status (all optional)
    """
    password = serializers.CharField(write_only=True, required=False, min_length=6)
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'full_name',
            'contact_no',
            'password',
            'profile_image',
            'status',
        ]

    def validate_contact_no(self, value):
        """Validate contact number length"""
        if len(value) < 10:
            raise serializers.ValidationError("Contact number must be at least 10 digits")
        if len(value) > 15:
            raise serializers.ValidationError("Contact number cannot exceed 15 digits")
        return value

    def validate_status(self, value):
        """Validate status is either 0 or 1"""
        if value not in [0, 1]:
            raise serializers.ValidationError("Status must be 0 (Inactive) or 1 (Active)")
        return value
