# Profile Management APIs

## Overview

The Profile Management APIs provide comprehensive user registration, retrieval, and update functionality with image upload support. These APIs handle user profile information including name, contact details, email, password, and profile images.

---

## API Endpoints

### 1. Register User with Profile

Registers a new user account with optional profile image upload.

#### Request

```
POST /api/profile/register/
```

**Content-Type:** `multipart/form-data` (for file upload)

#### Payload

**Form Data:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | string | Yes | User's full name (max 255 chars) |
| `email` | string | Yes | Email address (must be unique) |
| `contact_no` | string | Yes | Phone number (10-15 digits) |
| `password` | string | Yes | Password (min 6 characters) |
| `profile_image` | file | No | JPG/PNG image file (optional) |

**Example Request (cURL):**

```bash
curl -X POST http://localhost:8000/api/profile/register/ \
  -F "full_name=John Doe" \
  -F "email=john@example.com" \
  -F "contact_no=9876543210" \
  -F "password=SecurePass123" \
  -F "profile_image=@/path/to/image.jpg"
```

**Example Request (JSON - without file):**

```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "contact_no": "9876543210",
  "password": "SecurePass123"
}
```

#### Success Response (201 Created)

```json
{
  "status": true,
  "message": "User registered successfully",
  "data": {
    "user_id": 1,
    "full_name": "John Doe",
    "email": "john@example.com",
    "profile_image": "http://localhost:8000/media/profiles/user_1_profile.jpg"
  }
}
```

#### Error Response (400 - Validation Failed)

```json
{
  "status": false,
  "message": "Validation failed",
  "data": {
    "email": ["User with this email already exists"],
    "contact_no": ["Contact number must be at least 10 digits"],
    "password": ["This field may not be blank."]
  }
}
```

#### Error Response (400 - Email Already Exists)

```json
{
  "status": false,
  "message": "User with this email already exists",
  "statusCode": 400
}
```

#### Validation Rules

- ✅ Email must be unique in system
- ✅ Email must be valid format
- ✅ Contact number must be 10-15 digits
- ✅ Password must be at least 6 characters
- ✅ Full name must not be empty
- ✅ Profile image is optional (JPG/PNG only)
- ✅ Image size limit applies (default Django Pillow limits)

---

### 2. Get User Profile by ID

Retrieves complete user profile information including profile image.

#### Request

```
GET /api/profile/<user_id>/
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID |

**Query Parameters:** None

**Authentication:** Not required for this endpoint

### Success Response (200 OK)

```json
{
  "status": true,
  "message": "User profile retrieved successfully",
  "data": {
    "id": 1,
    "full_name": "John Doe",
    "email": "john@example.com",
    "contact_no": "9876543210",
    "status": 1,
    "is_active": true,
    "created_at": "2026-02-05T10:30:00Z",
    "updated_at": "2026-02-05T10:30:00Z",
    "role": {
      "id": 1,
      "name": "ADMIN"
    },
    "profile_image_url": "http://localhost:8000/media/profiles/user_1_profile.jpg"
  }
}
```

#### Error Response (404 - User Not Found)

```json
{
  "status": false,
  "message": "User not found",
  "statusCode": 404
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | User ID |
| `full_name` | string | User's full name |
| `email` | string | Email address |
| `contact_no` | string | Contact number |
| `status` | integer | 0=Inactive, 1=Active |
| `is_active` | boolean | Account active status |
| `created_at` | datetime | Account creation timestamp |
| `updated_at` | datetime | Last update timestamp |
| `role` | object | User's assigned role |
| `profile_image_url` | string | URL to profile image (null if none) |

---

### 3. Update User Profile

Updates user profile information including password and image.

#### Request

```
PUT /api/profile/<user_id>/update/
```

**Content-Type:** `multipart/form-data` (for file upload)

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID |

**Authentication:** Not required (but recommended for security)

#### Payload

**Form Data (all optional):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | string | No | Updated full name |
| `contact_no` | string | No | Updated phone number |
| `password` | string | No | New password (min 6 chars) |
| `profile_image` | file | No | New profile image file |
| `status` | integer | No | 0=Inactive, 1=Active |

**Example Request (cURL):**

```bash
curl -X PUT http://localhost:8000/api/profile/1/update/ \
  -F "full_name=Jane Doe" \
  -F "contact_no=9876543211" \
  -F "password=NewSecurePass123" \
  -F "profile_image=@/path/to/new_image.jpg" \
  -F "status=1"
```

**Example Request (JSON - partial update):**

```json
{
  "full_name": "Jane Doe",
  "contact_no": "9876543211"
}
```

#### Success Response (200 OK)

```json
{
  "status": true,
  "message": "User profile updated successfully",
  "data": {
    "id": 1,
    "full_name": "Jane Doe",
    "email": "john@example.com",
    "contact_no": "9876543211",
    "status": 1,
    "is_active": true,
    "created_at": "2026-02-05T10:30:00Z",
    "updated_at": "2026-02-05T11:45:00Z",
    "role": {
      "id": 1,
      "name": "ADMIN"
    },
    "profile_image_url": "http://localhost:8000/media/profiles/user_1_profile_new.jpg"
  }
}
```

#### Error Response (400 - Validation Failed)

```json
{
  "status": false,
  "message": "Validation failed",
  "data": {
    "contact_no": ["Contact number must be at least 10 digits"],
    "status": ["Status must be 0 (Inactive) or 1 (Active)"]
  }
}
```

#### Error Response (404 - User Not Found)

```json
{
  "status": false,
  "message": "User not found",
  "statusCode": 404
}
```

#### Validation Rules

- ✅ Contact number (if provided) must be 10-15 digits
- ✅ Password (if provided) must be at least 6 characters
- ✅ Status must be 0 or 1
- ✅ Profile image is optional (old image auto-deleted before new upload)
- ✅ All fields are optional (supports partial updates)
- ✅ Can update password without changing other fields

---

## Image Handling

### Upload Requirements

**Supported Formats:**
- JPG/JPEG
- PNG

**Size Limits:**
- Default: Up to 5MB (Django Pillow defaults)
- Path: `/media/profiles/`

### Image Behavior

**During Registration:**
- If image provided → Saved to user profile
- If image not provided → profile_image field remains empty

**During Update:**
- If new image provided → Old image deleted automatically, new one saved
- If no image in request → Current image remains unchanged

### Image URL Structure

```
Full URL: http://localhost:8000/media/profiles/user_<id>_<timestamp>.jpg
Base Path: /media/profiles/
```

---

## User Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 0 | Inactive | User account disabled |
| 1 | Active | User account active |

---

## Workflow Examples

### Example 1: Register New User with Image

```bash
# Step 1: Register with profile image
POST /api/profile/register/
{
  "full_name": "Alice Smith",
  "email": "alice@example.com",
  "contact_no": "8765432109",
  "password": "SecurePass@123",
  "profile_image": <file>
}

Response:
{
  "user_id": 5,
  "profile_image": "http://localhost:8000/media/profiles/user_5_profile.jpg"
}
```

### Example 2: Register Without Image, Add Later

```bash
# Step 1: Register without image
POST /api/profile/register/
{
  "full_name": "Bob Johnson",
  "email": "bob@example.com",
  "contact_no": "7654321098",
  "password": "SecurePass@456"
}

Response:
{
  "user_id": 6,
  "profile_image": null
}

# Step 2: Update profile with image
PUT /api/profile/6/update/
{
  "profile_image": <file>
}

Response:
{
  "profile_image_url": "http://localhost:8000/media/profiles/user_6_profile.jpg"
}
```

### Example 3: Update Multiple Fields

```bash
PUT /api/profile/1/update/
{
  "full_name": "John Updated",
  "contact_no": "9999999999",
  "password": "NewPassword@789",
  "status": 1
}

Response:
{
  "full_name": "John Updated",
  "contact_no": "9999999999",
  "status": 1,
  "password_updated": true  // Implicit confirmation
}
```

---

## Error Codes

| Code | Meaning | Example |
|------|---------|---------|
| 201 | Created | User successfully registered |
| 200 | OK | Profile retrieved/updated |
| 400 | Bad Request | Invalid input, email exists, validation failed |
| 404 | Not Found | User not found |

---

## Data Models

### User Profile Object

```json
{
  "id": 1,
  "full_name": "string (255)",
  "email": "string (unique, valid email)",
  "contact_no": "string (10-15 digits)",
  "status": "integer (0 or 1)",
  "is_active": "boolean",
  "profile_image": "ImageField (nullable)",
  "profile_image_url": "string (url)",
  "created_at": "datetime",
  "updated_at": "datetime",
  "role": {
    "id": "integer",
    "name": "string"
  }
}
```

---

## Security Considerations

1. **Password Hashing**
   - Passwords are hashed using Django's default hasher
   - Original password never stored

2. **Email Uniqueness**
   - Email field has unique constraint
   - Prevents duplicate registrations

3. **File Upload Security**
   - Only image files allowed
   - Stored outside web root
   - Auto-deleted when replaced

4. **Image Path Randomization**
   - Filenames include user ID and timestamp
   - Prevents direct path guessing

---

## Best Practices

1. **Validation Before Submit**
   - Validate email format on frontend
   - Validate phone number format
   - Check password strength

2. **Image Upload**
   - Compress images before upload
   - Show upload progress to user
   - Validate file type on client-side

3. **Error Handling**
   - Display validation errors to user
   - Suggest fixes for phone/email issues
   - Provide retry option on failure

4. **Password Security**
   - Enforce minimum password requirements
   - Show password strength indicator
   - Never transmit in plain text (use HTTPS)

---

## Migration from Old APIs

If migrating from a previous user management API:

**Old Endpoint** → **New Endpoint**
- POST /api/users/create/ → POST /api/profile/register/
- GET /api/users/{id}/ → GET /api/profile/{id}/
- PUT /api/users/{id}/update/ → PUT /api/profile/{id}/update/

**Key Differences:**
- Profile APIs include image handling
- Better validation messages
- Consistent response format

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Email already exists" | Use unique email address |
| "Contact number invalid" | Ensure 10-15 digits only |
| "Image upload failed" | Use JPG/PNG format, <5MB |
| "User not found" | Verify correct user ID |
| "Validation failed" | Check all required fields populated |
| "Password too short" | Password must be 6+ characters |

---

## Rate Limiting

No specific rate limits defined. Standard Django/DRF rate limiting applies if configured.

---

## Notes

- All datetime fields in UTC (ISO 8601 format)
- Profile images stored in `/media/profiles/` directory
- Old images automatically deleted when replaced
- Email validation follows RFC 5322 standards
- Phone numbers accept digits and common formatting characters

---

**Last Updated:** February 5, 2026
