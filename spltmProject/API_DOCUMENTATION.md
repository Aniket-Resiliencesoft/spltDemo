# API Documentation

## Table of Contents
1. [Reset Password APIs](#reset-password-apis)
2. [Event Collections APIs](#event-collections-apis)
3. [Event Management APIs](#event-management-apis)

---

## Reset Password APIs

### 1. Reset Password Request
Request OTP for password reset by providing email or contact number.

**Endpoint:** `POST /api/auth/reset-password/request/`

**Authentication:** Not required

**Request Headers:**
```
Content-Type: application/json
```

**Request Payload:**
```json
{
  "identifier": "user@example.com"
}
```

OR

```json
{
  "identifier": "9876543210"
}
```

**Response (Success - 200):**
```json
{
  "IsSuccess": true,
  "Message": "OTP sent to your email. Please verify to reset password.",
  "Data": {
    "user_id": 1,
    "email": "user@example.com",
    "otp_generated": true,
    "email_status": "success",
    "email_message": "Email sent successfully"
  }
}
```

**Response (Error - 404):**
```json
{
  "IsSuccess": false,
  "Message": "User not found with the provided email or contact number",
  "Data": null
}
```

**Notes:**
- OTP is valid for 10 minutes
- User identified by email OR contact number (whichever is provided)
- Updates user's OTP field in database

---

### 2. Reset Password Verify OTP
Verify OTP and reset the user's password.

**Endpoint:** `POST /api/auth/reset-password/verify-otp/`

**Authentication:** Not required

**Request Headers:**
```
Content-Type: application/json
```

**Request Payload (Using user_id):**
```json
{
  "user_id": 1,
  "otp": "123456",
  "new_password": "NewPassword@123",
  "confirm_password": "NewPassword@123"
}
```

OR **(Using email):**
```json
{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "NewPassword@123",
  "confirm_password": "NewPassword@123"
}
```

**Response (Success - 200):**
```json
{
  "IsSuccess": true,
  "Message": "Password reset successfully",
  "Data": {
    "user_id": 1,
    "email": "user@example.com",
    "message": "Your password has been reset successfully"
  }
}
```

**Response (Error - 401):**
```json
{
  "IsSuccess": false,
  "Message": "Invalid or expired OTP. Please request a new OTP.",
  "Data": null
}
```

**Response (Error - 404):**
```json
{
  "IsSuccess": false,
  "Message": "User not found",
  "Data": null
}
```

**Validation Rules:**
- ✅ Either `user_id` OR `email` must be provided
- ✅ OTP must be 6 digits
- ✅ OTP must not be expired (10 minutes)
- ✅ `new_password` and `confirm_password` must match
- ✅ Password minimum length: 6 characters
- ✅ OTP is cleared from database after successful verification

---

## Event Collections APIs

### 1. Creator Event Collections Summary
Get all events created by the authenticated user with financial summary.

**Endpoint:** `GET /api/events/my-collections/`

**Authentication:** Required (JWT Token)

**Request Headers:**
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

**Request Parameters:** None

**Response (Success - 200):**
```json
{
  "IsSuccess": true,
  "Message": "Creator events and collections retrieved successfully",
  "Data": {
    "events": [
      {
        "event_id": 1,
        "title": "Trip to Goa",
        "event_date": "2026-02-15",
        "total_event_amount": "50000.00",
        "event_total_collected": "25000.00",
        "event_total_spend": "5000.00",
        "my_wallet": "20000.00",
        "status": "active"
      },
      {
        "event_id": 2,
        "title": "Birthday Party",
        "event_date": "2026-02-20",
        "total_event_amount": "10000.00",
        "event_total_collected": "9000.00",
        "event_total_spend": "8000.00",
        "my_wallet": "1000.00",
        "status": "completed"
      }
    ],
    "total_collected_all_events": "34000.00",
    "total_spend_all_events": "13000.00",
    "total_wallet_balance": "21000.00",
    "events_count": 2
  }
}
```

**Field Descriptions:**
- `event_total_collected`: Total amount collected from participants
- `event_total_spend`: Total amount paid to vendors
- `my_wallet`: Available balance = (collected - spend)
- `total_wallet_balance`: Overall available balance across all events

---

## Event Management APIs

### 1. List All Events (Updated)
Retrieve all events with pagination, filters, and spending information.

**Endpoint:** `GET /api/events/`

**Authentication:** Required (JWT Token)

**Request Headers:**
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

**Query Parameters:**
```
pageNo=1              (Optional, default: 1)
pageSize=10           (Optional, default: 10)
fromDate=2026-02-01   (Optional, format: YYYY-MM-DD)
toDate=2026-02-28     (Optional, format: YYYY-MM-DD)
status=active         (Optional: created, active, closed, completed, cancelled)
category=trip         (Optional: turf, restaurant, trip, party, custom)
search=Goa            (Optional, searches in title and description)
```

**Response (Success - 200):**
```json
{
  "IsSuccess": true,
  "Message": "Events retrieved successfully",
  "Data": {
    "pagination": {
      "pageNo": 1,
      "pageSize": 10,
      "totalRecord": 5
    },
    "data": [
      {
        "event_id": 1,
        "title": "Trip to Goa",
        "category": "trip",
        "description": "Weekend getaway to Goa",
        "event_date": "2026-02-15",
        "start_date_time": "2026-02-15T10:00:00Z",
        "end_date_time": "2026-02-17T18:00:00Z",
        "total_event_amount": 50000.00,
        "participants_count": 5,
        "total_contributed": 25000.00,
        "total_spend": 5000.00,
        "IsRechargeRequired": true,
        "event_status": "active",
        "created_by_id": 1
      },
      {
        "event_id": 2,
        "title": "Restaurant Bill",
        "category": "restaurant",
        "description": "Dinner with friends",
        "event_date": "2026-02-14",
        "start_date_time": "2026-02-14T19:00:00Z",
        "end_date_time": "2026-02-14T22:00:00Z",
        "total_event_amount": 5000.00,
        "participants_count": 4,
        "total_contributed": 4500.00,
        "total_spend": 500.00,
        "IsRechargeRequired": true,
        "event_status": "completed",
        "created_by_id": 2
      }
    ]
  }
}
```

**Field Descriptions:**
- `total_contributed`: Total amount collected from participants (completed transactions)
- `total_spend`: Total amount paid to vendors (processing, completed, processed payouts)
- `IsRechargeRequired`: Boolean flag - `true` if there's available balance (collected > spend)

**Usage Examples:**

**Example 1: Get active events created by user**
```
GET /api/events/?status=active&pageNo=1&pageSize=10
```

**Example 2: Get events within date range**
```
GET /api/events/?fromDate=2026-02-01&toDate=2026-02-28
```

**Example 3: Search events**
```
GET /api/events/?search=Goa&category=trip
```

---

### 2. Create Event (Updated)
Create a new event with optional due payment date requirements.

**Endpoint:** `POST /api/events/create/`

**Authentication:** Required (JWT Token)

**Request Headers:**
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

**Request Payload (Option 1: Due pay before event start - MANDATORY):**
```json
{
  "title": "Trip to Goa",
  "category": "trip",
  "description": "Weekend getaway to Goa beaches",
  "event_date": "2026-02-15",
  "start_date_time": "2026-02-15T10:00:00Z",
  "end_date_time": "2026-02-17T18:00:00Z",
  "due_pay_date_time": "2026-02-14T23:59:59Z",
  "due_pay_before_event_start": true,
  "latitude": 15.3017,
  "longitude": 73.8207,
  "location": "Goa, India",
  "persons_count": 5,
  "event_amount": 50000.00,
  "status": "draft",
  "vendor_name": "Hotel Paradise",
  "custom_category": null
}
```

**Request Payload (Option 2: Due pay after event start - OPTIONAL):**
```json
{
  "title": "Trip to Goa",
  "category": "trip",
  "description": "Weekend getaway to Goa beaches",
  "event_date": "2026-02-15",
  "start_date_time": "2026-02-15T10:00:00Z",
  "end_date_time": "2026-02-17T18:00:00Z",
  "due_pay_date_time": null,
  "due_pay_before_event_start": false,
  "latitude": 15.3017,
  "longitude": 73.8207,
  "location": "Goa, India",
  "persons_count": 5,
  "event_amount": 50000.00,
  "status": "draft",
  "vendor_name": "Hotel Paradise",
  "custom_category": null
}
```

**Response (Success - 201):**
```json
{
  "IsSuccess": true,
  "Message": "Event created successfully",
  "Data": {
    "id": 1,
    "title": "Trip to Goa",
    "category": "trip",
    "category_display": "Trip booking",
    "description": "Weekend getaway to Goa beaches",
    "event_date": "2026-02-15",
    "start_date_time": "2026-02-15T10:00:00Z",
    "end_date_time": "2026-02-17T18:00:00Z",
    "due_pay_date_time": "2026-02-14T23:59:59Z",
    "due_pay_before_event_start": true,
    "latitude": 15.3017,
    "longitude": 73.8207,
    "location": "Goa, India",
    "persons_count": 5,
    "event_amount": 50000.00,
    "per_person_amount": 10000.00,
    "status": "draft",
    "status_display": "Draft",
    "created_by": 1,
    "created_by_name": "John Doe",
    "created_at": "2026-02-06T12:00:00Z",
    "updated_at": "2026-02-06T12:00:00Z",
    "is_active": true,
    "vendor_name": "Hotel Paradise",
    "custom_category": null
  }
}
```

**Response (Error - 400):**
```json
{
  "IsSuccess": false,
  "Message": "Validation failed",
  "Data": {
    "due_pay_date_time": [
      "Due pay date is mandatory when 'due_pay_before_event_start' is True."
    ],
    "start_date_time": [
      "Start datetime must be before end datetime."
    ]
  }
}
```

**Validation Rules:**
- ✅ `title`: Required, max 200 characters
- ✅ `category`: Required (turf, restaurant, trip, party, custom)
- ✅ `event_date`: Required, must be valid date
- ✅ `start_date_time`: Required, must be before `end_date_time`
- ✅ `end_date_time`: Required, must be after `start_date_time`
- ✅ `due_pay_before_event_start`: Optional, default is `true`
  - If `true`: `due_pay_date_time` is **MANDATORY** and must be ≤ `start_date_time`
  - If `false`: `due_pay_date_time` is **OPTIONAL** (can be null)
- ✅ `due_pay_date_time`: Must not be after `event_date`
- ✅ `persons_count`: Required, minimum 1
- ✅ `event_amount`: Required, minimum 0.01

---

## Common Response Format

All API responses follow this structure:

**Success Response:**
```json
{
  "IsSuccess": true,
  "Message": "Operation successful",
  "Data": { /* Response data */ }
}
```

**Error Response:**
```json
{
  "IsSuccess": false,
  "Message": "Error description",
  "Data": null
}
```

---

## Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Validation error |
| 401 | Unauthorized - Invalid/missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |

---

## Authentication

JWT token is required for most endpoints (except reset password APIs).

**How to get JWT token:**
1. Call `/api/auth/login/` with email and password
2. Receive `access_token` in response
3. Add to headers: `Authorization: Bearer <access_token>`

---

## Error Messages

Common validation error messages:

| Error | Description |
|-------|-------------|
| Invalid input data | Request validation failed |
| User not found | User doesn't exist |
| Invalid or expired OTP | OTP is incorrect or expired (10 min limit) |
| Passwords must match | new_password ≠ confirm_password |
| Due pay date is mandatory | `due_pay_before_event_start=true` but no date provided |
| Start must be before end | Event start_datetime ≥ end_datetime |
| Persons count must be at least 1 | Invalid participant count |
| Insufficient wallet balance | Not enough funds for payout |

---

## Date Format

All dates use ISO 8601 format:
- **Date**: `YYYY-MM-DD` (e.g., `2026-02-15`)
- **DateTime**: `YYYY-MM-DDTHH:MM:SSZ` (e.g., `2026-02-15T10:00:00Z`)

---

## Examples Using cURL

### Example 1: Request Password Reset OTP
```bash
curl -X POST http://localhost:8000/api/auth/reset-password/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "user@example.com"
  }'
```

### Example 2: Verify Reset OTP and Change Password
```bash
curl -X POST http://localhost:8000/api/auth/reset-password/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "otp": "123456",
    "new_password": "NewPassword@123",
    "confirm_password": "NewPassword@123"
  }'
```

### Example 3: Get Creator Event Collections
```bash
curl -X GET http://localhost:8000/api/events/my-collections/ \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json"
```

### Example 4: Get Events with Filters
```bash
curl -X GET "http://localhost:8000/api/events/?status=active&pageNo=1&pageSize=10" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json"
```

### Example 5: Create Event
```bash
curl -X POST http://localhost:8000/api/events/create/ \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Trip to Goa",
    "category": "trip",
    "event_date": "2026-02-15",
    "start_date_time": "2026-02-15T10:00:00Z",
    "end_date_time": "2026-02-17T18:00:00Z",
    "due_pay_date_time": "2026-02-14T23:59:59Z",
    "due_pay_before_event_start": true,
    "persons_count": 5,
    "event_amount": 50000.00,
    "status": "draft"
  }'
```

---

## Last Updated
February 6, 2026
