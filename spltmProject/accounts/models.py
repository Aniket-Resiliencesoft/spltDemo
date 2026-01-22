from django.db import models
from common.models import BaseModel 

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
    
    class Meta:
        db_table = "users"

class UserRole(BaseModel):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    role = models.ForeignKey('Role', on_delete=models.CASCADE)

    class Meta:
        db_table = "user_roles"
        unique_together = ('user', 'role')


