📘 Project Setup Documentation

Project Name: SplitMoney
Technology Stack: Python 3.10, Django 5.2, Django REST Framework, SQL Server
Architecture: UI + API (AJAX-based), Custom Authentication & Authorization

🔹 Step 1: Project & Environment Setup
1.1 Create Virtual Environment
python -m venv spltEnv


Activate:

spltEnv\Scripts\activate

1.2 Install Required Packages
pip install django djangorestframework mssql-django pyodbc

1.3 Create Django Project
django-admin startproject spltmProject
cd spltmProject

1.4 Create Applications
python manage.py startapp common
python manage.py startapp accounts

1.5 Register Apps in settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',

    'common',
    'accounts',
]

🔹 Step 2: SQL Server Configuration (Windows Authentication)
2.1 Database Configuration (settings.py)
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'db_splitMoney',
        'HOST': 'localhost',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'trusted_connection': 'yes',
            'trust_server_certificate': 'yes',
        },
    }
}

2.2 Database Preparation (SQL Server)
CREATE DATABASE db_splitMoney;


Grant access:

USE db_splitMoney;

CREATE USER [LAPTOP-JFDQA64T\ASUS] FOR LOGIN [LAPTOP-JFDQA64T\ASUS];
ALTER ROLE db_owner ADD MEMBER [LAPTOP-JFDQA64T\ASUS];

🔹 Step 3: Global Base Model (Reusable Across Modules)
3.1 Create Base Model (common/models.py)
from django.db import models

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


✔ Used across all modules
✔ No database table created
✔ Avoids repetitive fields

🔹 Step 4: Custom Authentication Models
4.1 Role Model
class Role(BaseModel):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "roles"

4.2 User Model
class User(BaseModel):
    STATUS_CHOICES = (
        (0, 'Inactive'),
        (1, 'Active'),
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    contact_no = models.CharField(max_length=15)
    password_hash = models.CharField(max_length=255)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)

    class Meta:
        db_table = "users"

4.3 User–Role Mapping Model
class UserRole(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        db_table = "user_roles"
        unique_together = ('user', 'role')

🔹 Step 5: Migrations
5.1 Create Migrations
python manage.py makemigrations

5.2 Apply Migrations
python manage.py migrate


✔ Tables created successfully
✔ Schema managed via Django ORM
✔ Database-agnostic (SQL Server → MySQL ready)