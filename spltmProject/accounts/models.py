from django.db import models
from common.models import BaseModel 
import random
from datetime import timedelta
from django.utils import timezone

class Role(BaseModel):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "roles"

class User(BaseModel):
    STATUS_CHOICES = (
        (0, 'Inactive'),
        (1, 'Active'),
    )

    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    contact_no = models.CharField(max_length=15)
    password_hash = models.CharField(max_length=255)
    profile_image = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    last_login = models.DateTimeField(null=True, blank=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_generated_at = models.DateTimeField(null=True, blank=True)
    
    def generate_otp(self):
        """
        Generate a 6-digit OTP and save it to the database.
        OTP is valid for 10 minutes.
        """
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.otp = otp
        self.otp_generated_at = timezone.now()
        self.save()
        return otp
    
    def verify_otp(self, provided_otp):
        """
        Verify if the provided OTP is correct and not expired.
        OTP expires after 10 minutes.
        """
        if not self.otp or not self.otp_generated_at:
            return False
        
        # Check if OTP matches
        if self.otp != provided_otp:
            return False
        
        # Check if OTP is expired (10 minutes)
        expiry_time = self.otp_generated_at + timedelta(minutes=10)
        if timezone.now() > expiry_time:
            return False
        
        # Clear OTP after successful verification
        self.otp = None
        self.otp_generated_at = None
        self.save()
        return True
    
    class Meta:
        db_table = "users"

class UserRole(BaseModel):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    role = models.ForeignKey('Role', on_delete=models.CASCADE)

    class Meta:
        db_table = "user_roles"
        unique_together = ('user', 'role')


