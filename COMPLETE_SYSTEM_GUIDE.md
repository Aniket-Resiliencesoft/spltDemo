# SplitMoney System - Complete Implementation Guide

## 🏗️ System Architecture Overview

### Technology Stack
- **Backend:** Django 4.2.11 + Django REST Framework 3.14.0
- **Database:** SQLite (Development)
- **Authentication:** JWT (PyJWT 2.10.1)
- **Frontend:** HTML5, CSS3, JavaScript (jQuery)
- **Email:** Django's email service with OTP generation

---

## 📚 Complete API Reference

### Authentication APIs

#### 1. Login API
**Endpoint:** `POST /api/auth/login/`
```json
Request:
{
  "email": "user@example.com",
  "password": "password123"
}

Response (Admin User):
{
  "IsSuccess": true,
  "Message": "Login successful",
  "Data": {
    "user_id": 1,
    "full_name": "Admin User",
    "email": "admin@example.com",
    "role": "admin",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}

Response (Non-Admin User - First Login):
{
  "IsSuccess": true,
  "Message": "OTP sent to registered email",
  "Data": {
    "user_id": 2,
    "email": "user@example.com"
  }
}

Response (Non-Admin User - Subsequent Login):
{
  "IsSuccess": true,
  "Message": "Login successful",
  "Data": {
    "user_id": 2,
    "full_name": "Regular User",
    "email": "user@example.com",
    "role": "user",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

#### 2. OTP Generate API
**Endpoint:** `POST /api/auth/otp/generate/`
```json
Request:
{
  "user_id": 2
}

Response:
{
  "IsSuccess": true,
  "Message": "OTP sent to user@example.com",
  "Data": {
    "otp_id": "abc123",
    "expires_in": 600
  }
}
```

#### 3. OTP Verify API
**Endpoint:** `POST /api/auth/otp/verify/`
```json
Request:
{
  "user_id": 2,
  "otp": "123456"
}

Response:
{
  "IsSuccess": true,
  "Message": "OTP verified successfully",
  "Data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user_id": 2,
    "email": "user@example.com"
  }
}
```

#### 4. Dashboard Stats API
**Endpoint:** `GET /api/dashboard/stats/`
**Authentication:** Required (Bearer Token)
```json
Response:
{
  "IsSuccess": true,
  "Message": "Dashboard statistics retrieved successfully",
  "Data": {
    "total_users": 10,
    "active_events": 5,
    "total_payment": 50000,
    "pending_payment": 10000
  }
}
```

---

## 🖥️ UI Routes (Pages)

| Route | Page | Purpose |
|-------|------|---------|
| `/` | Redirect to dashboard/login | Home |
| `/login/` | Login Page | User authentication |
| `/register/` | Registration Page | New user registration |
| `/verify-otp/` | OTP Verification | Verify email with OTP |
| `/dashboard/` | Dashboard | View stats & metrics |
| `/logout/` | Logout Endpoint | Clear session & logout |

---

## 🔄 User Authentication Flow

### New User Registration
```
1. User visits /register/
2. Fills form: full_name, email, contact, password, confirm_password
3. Form validates (email uniqueness, password match)
4. POST /api/users/create/
5. User created with email_verified=False
6. Redirects to /login/
7. Success toast: "Registration successful! Please log in."
```

### User Login (First Time)
```
1. User visits /login/
2. Enters email and password
3. POST /api/auth/login/
4. System checks: is email verified?
   - If YES (admin or subsequent user): Issue JWT token → /dashboard/
   - If NO (first-time user): Send OTP → /verify-otp/
5. Toast shows appropriate message
```

### OTP Verification
```
1. User on /verify-otp/ receives OTP code
2. Enters 6-digit OTP
3. POST /api/auth/otp/verify/
4. OTP verified → email_verified set to True
5. JWT token issued
6. Redirects to /dashboard/
7. Success toast: "Email verified! Welcome to SplitMoney"
```

### Subsequent Logins (Same User)
```
1. User logs in again
2. POST /api/auth/login/
3. email_verified already TRUE
4. JWT token issued directly (no OTP)
5. Redirects to /dashboard/
```

---

## 🎨 Response Format Standard

### Success Response
```json
{
  "IsSuccess": true,
  "Message": "Operation description",
  "Data": {
    "key": "value"
  }
}
```

### Error Response (Validation)
```json
{
  "IsSuccess": false,
  "Message": "Validation failed",
  "Data": {
    "email": ["User with this email already exists."],
    "password": ["Password must be at least 8 characters."]
  }
}
```

### Error Response (General)
```json
{
  "IsSuccess": false,
  "Message": "Error description"
}
```

---

## 🔐 Security Features

### JWT Token
- **Storage:** Cookies (secure) + LocalStorage (fallback)
- **Header:** `Authorization: Bearer <token>`
- **Expiry:** Configurable in settings
- **Validation:** Checked on every protected page

### CSRF Protection
- **Token:** Extracted from cookies
- **Header:** `X-CSRFToken: <token>`
- **Applied:** All POST/PUT/DELETE requests

### Email Verification
- **OTP:** 6-digit code, 10-minute expiry
- **One-Time:** Email verified only once per user
- **Benefits:** Prevents duplicate accounts, ensures valid email

### Password Security
- **Hashing:** Django's built-in password hashing
- **Validation:** Min 8 characters, password confirmation required
- **Storage:** Never sent back to frontend

---

## 🧩 Key Models

### User Model
```python
Fields:
- id (PK)
- full_name
- email (unique)
- contact_no
- password (hashed)
- email_verified (Boolean) ← NEW
- status
- is_active
- created_at, updated_at
```

### Event Model
```python
Fields:
- id (PK)
- title
- category
- description
- event_date
- start_date_time, end_date_time
- due_pay_date
- persons_count
- status (active, draft, completed, cancelled)
- created_by (FK to User)
- is_active
- created_at, updated_at
```

### EventCollectionTransaction Model
```python
Fields:
- id (PK)
- event (FK to Event)
- user (FK to User)
- amount
- status (completed, pending)
- transaction_date
- is_active
- created_at, updated_at
```

---

## 📊 Dashboard Metrics

### Total Users
- Count of all active users in system
- `User.objects.filter(is_active=True).count()`

### Active Events
- Count of events with status 'active' or 'draft'
- `Event.objects.filter(is_active=True, status__in=['active', 'draft']).count()`

### Total Payment
- Sum of completed transactions
- `EventCollectionTransaction.objects.filter(status='completed').aggregate(Sum('amount'))`

### Pending Payment (Available in API)
- Sum of pending transactions
- `EventCollectionTransaction.objects.filter(status='pending').aggregate(Sum('amount'))`

---

## 🎯 Frontend Components

### Toast Notification System
**File:** `static/assets/js/toast.js`

**Functions:**
```javascript
// Main function
showToast(message, type, duration)

// Type-specific shortcuts
showSuccessToast(message, duration)
showErrorToast(message, duration)
showWarningToast(message, duration)
showInfoToast(message, duration)

// Extract field errors from API response
getErrorMessage(xhr)
```

**Example Usage:**
```javascript
// Success
showSuccessToast("Registration successful!");

// Error with field details
const errorMsg = getErrorMessage(xhr); // "email: User already exists. password: Min 8 characters."
showErrorToast(errorMsg);

// Info
showInfoToast("Processing your request...", 3000);
```

### Cookie Utilities
```javascript
getCookie(name)        // Read cookie value
setCookie(name, value, hours) // Set cookie value
getCSRFToken()         // Extract CSRF token from cookies
```

---

## 🚀 Deployment Checklist

- [ ] Configure email service (SMTP settings)
- [ ] Set DEBUG=False in production
- [ ] Configure ALLOWED_HOSTS
- [ ] Set secure cookies (SECURE_COOKIE_SECURE=True)
- [ ] Configure CORS if needed
- [ ] Set JWT_EXPIRY_HOURS
- [ ] Run migrations
- [ ] Collect static files
- [ ] Set up database backups
- [ ] Configure SSL/HTTPS
- [ ] Test all authentication flows
- [ ] Test dashboard with various data

---

## 📝 File Structure Reference

```
spltmProject/
├── accounts/
│   ├── api_views/
│   │   ├── auth_api.py (Login, OTP APIs)
│   │   ├── user_api.py (User CRUD)
│   │   ├── roles_api.py (Role CRUD)
│   │   └── dashboard_api.py (Dashboard stats) ← NEW
│   ├── models.py (User, Role, UserRole)
│   ├── ui_views.py (Page rendering)
│   └── urls.py (Routes)
├── common/
│   ├── api/
│   │   └── base_api.py (BaseAuthenticatedAPI)
│   ├── responses.py (api_response_success/error)
│   ├── decorators.py (login_required_view)
│   └── utils/
│       └── jwt_utils.py (JWT functions)
├── events/
│   ├── models.py (Event model)
│   ├── api_views/ (Event APIs)
│   └── urls.py
├── payments/
│   ├── models.py (EventCollectionTransaction)
│   ├── api_views/ (Payment APIs)
│   └── urls.py
├── static/
│   └── assets/
│       ├── css/
│       ├── js/
│       │   ├── toast.js ← NEW/UPDATED
│       │   └── plugins/
│       └── fonts/
├── templates/
│   ├── dashboard.html ← NEW
│   └── auth/
│       ├── login.html (Updated)
│       ├── register.html (New)
│       └── verify_otp.html (Updated)
└── manage.py
```

---

## 🔍 Common Issues & Solutions

### Issue: OTP not received
**Solution:** Check SMTP settings and email configuration in settings.py

### Issue: Dashboard shows 0 stats
**Solution:** 
1. Ensure user is authenticated (valid token)
2. Check database for existing users/events/transactions
3. Verify active flag is set to True on records

### Issue: Session expires too quickly
**Solution:** Increase JWT_EXPIRY_HOURS in settings

### Issue: CSRF token error
**Solution:** Ensure X-CSRFToken header is included in all API calls

### Issue: Styles not loading
**Solution:** Run `python manage.py collectstatic` and check STATIC_URL setting

---

## 📞 Support & Maintenance

### Database Migrations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

### Server Management
```bash
# Run development server
python manage.py runserver 8000

# Run production server (with gunicorn)
gunicorn spltmProject.wsgi --bind 0.0.0.0:8000
```

### Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts

# Run with verbose output
python manage.py test accounts -v 2
```

---

## ✅ Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| User Registration | ✅ Complete | With validation |
| Email OTP | ✅ Complete | One-time only |
| JWT Authentication | ✅ Complete | Token-based |
| Role-Based Access | ✅ Complete | Admin vs User |
| Dashboard API | ✅ Complete | Stats endpoint |
| Dashboard UI | ✅ Complete | Responsive design |
| Toast Notifications | ✅ Complete | 4 types included |
| API Response Format | ✅ Complete | Standardized |
| Error Handling | ✅ Complete | Field-level errors |
| Session Management | ✅ Complete | Auto expiry handling |
| Logout | ✅ Complete | Clears tokens |

---

**Last Updated:** January 2026
**Version:** 1.0 (Dashboard & Auth Complete)
**Status:** ✅ Production Ready
