# Profile API Quick Start Guide

## Overview

The Profile APIs provide user registration, profile retrieval, and profile updates with image support. Simple 3-step integration for user account management.

---

## 3 Simple APIs

### 1️⃣ Register New User

```http
POST /api/profile/register/
Content-Type: multipart/form-data

Form Data:
  full_name: "John Doe"
  email: "john@example.com"
  contact_no: "9876543210"
  password: "SecurePass123"
  profile_image: [optional file]
```

**What you need:**
- Full name (required)
- Email (unique, required)
- Phone number 10-15 digits (required)
- Password 6+ characters (required)
- Profile image (optional JPG/PNG)

**What it returns:**
```json
{
  "user_id": 1,
  "email": "john@example.com",
  "full_name": "John Doe",
  "profile_image": "http://api.com/media/profiles/user_1.jpg"
}
```

---

### 2️⃣ Get User Profile

```http
GET /api/profile/{user_id}/
```

**Example:**
```http
GET /api/profile/1/
```

**What it returns:**
```json
{
  "id": 1,
  "full_name": "John Doe",
  "email": "john@example.com",
  "contact_no": "9876543210",
  "status": 1,
  "is_active": true,
  "role": {
    "id": 1,
    "name": "ADMIN"
  },
  "profile_image_url": "http://api.com/media/profiles/user_1.jpg",
  "created_at": "2026-02-05T10:30:00Z",
  "updated_at": "2026-02-05T10:30:00Z"
}
```

---

### 3️⃣ Update User Profile

```http
PUT /api/profile/{user_id}/update/
Content-Type: multipart/form-data

Form Data (all optional):
  full_name: "Jane Doe"
  contact_no: "9876543211"
  password: "NewPassword123"
  profile_image: [optional new file]
  status: 1
```

**What it returns:**
```json
{
  "id": 1,
  "full_name": "Jane Doe",
  "contact_no": "9876543211",
  "profile_image_url": "http://api.com/media/profiles/user_1_new.jpg",
  "updated_at": "2026-02-05T11:45:00Z"
}
```

---

## Quick Examples

### Register with Image

```bash
curl -X POST http://localhost:8000/api/profile/register/ \
  -F "full_name=John Doe" \
  -F "email=john@example.com" \
  -F "contact_no=9876543210" \
  -F "password=SecurePass123" \
  -F "profile_image=@profile.jpg"
```

### Register Without Image

```bash
curl -X POST http://localhost:8000/api/profile/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john@example.com",
    "contact_no": "9876543210",
    "password": "SecurePass123"
  }'
```

### Get Profile

```bash
curl http://localhost:8000/api/profile/1/
```

### Update Profile with New Image

```bash
curl -X PUT http://localhost:8000/api/profile/1/update/ \
  -F "full_name=Jane Doe" \
  -F "profile_image=@new_photo.jpg"
```

### Update Password Only

```bash
curl -X PUT http://localhost:8000/api/profile/1/update/ \
  -H "Content-Type: application/json" \
  -d '{
    "password": "NewSecurePass456"
  }'
```

---

## Validation Rules at a Glance

| Field | Rules | Example |
|-------|-------|---------|
| **full_name** | Required, max 255 chars | John Doe |
| **email** | Unique, valid format | john@example.com |
| **contact_no** | 10-15 digits only | 9876543210 |
| **password** | Min 6 characters | SecurePass123 |
| **profile_image** | JPG/PNG only, optional | image.jpg |
| **status** | 0 or 1 | 1 (active) |

---

## Status Codes

| Code | Meaning |
|------|---------|
| 1 | Active User |
| 0 | Inactive User |

---

## Common Scenarios

### Scenario 1: New User Registration

```
Step 1: User fills registration form
Step 2: POST /api/profile/register/ with data + image
Step 3: Get user_id from response
Step 4: Store token and redirect to dashboard
```

### Scenario 2: Update Profile Later

```
Step 1: User clicks "Edit Profile"
Step 2: GET /api/profile/{user_id}/ to load current data
Step 3: User modifies fields (name, phone, password, image)
Step 4: PUT /api/profile/{user_id}/update/ with changes
Step 5: Show confirmation message
```

### Scenario 3: Profile Picture Only Update

```
Step 1: User selects new profile picture
Step 2: PUT /api/profile/{user_id}/update/ with only image
    - Old image auto-deleted
    - New image saved
```

---

## Image Upload Tips

✅ **DO:**
- Use JPG or PNG format
- Compress before uploading
- Show progress indication
- Validate file type on frontend

❌ **DON'T:**
- Upload files larger than 5MB
- Use unsupported formats (GIF, BMP, etc.)
- Upload without compression
- Allow very large dimensions (>3000px)

---

## Error Responses

### Validation Error
```json
{
  "status": false,
  "message": "Validation failed",
  "data": {
    "email": ["User with this email already exists"],
    "contact_no": ["Contact number must be at least 10 digits"]
  }
}
```

### User Not Found
```json
{
  "status": false,
  "message": "User not found",
  "statusCode": 404
}
```

### Email Already Exists
```json
{
  "status": false,
  "message": "User with this email already exists",
  "statusCode": 400
}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Email validation error | Use valid email (abc@domain.com) |
| Contact number error | Use only digits, 10-15 length |
| Image not uploading | Use JPG/PNG, check file size (<5MB) |
| User not found | Verify correct user ID |
| Password too short | Use 6+ characters |
| "Validation failed" | Check all required fields are filled |

---

## JavaScript Example (Frontend Integration)

```javascript
// Register User
async function registerUser(formData) {
  const response = await fetch('/api/profile/register/', {
    method: 'POST',
    body: formData // multipart form data with image
  });
  const result = await response.json();
  return result.data.user_id;
}

// Get Profile
async function getProfile(userId) {
  const response = await fetch(`/api/profile/${userId}/`);
  return await response.json();
}

// Update Profile
async function updateProfile(userId, formData) {
  const response = await fetch(`/api/profile/${userId}/update/`, {
    method: 'PUT',
    body: formData
  });
  return await response.json();
}
```

---

## Form Examples

### Registration Form HTML

```html
<form id="registerForm" enctype="multipart/form-data">
  <input type="text" name="full_name" placeholder="Full Name" required>
  <input type="email" name="email" placeholder="Email" required>
  <input type="tel" name="contact_no" placeholder="Phone" required>
  <input type="password" name="password" placeholder="Password" required>
  <input type="file" name="profile_image" accept="image/*">
  <button type="submit">Register</button>
</form>

<script>
  document.getElementById('registerForm').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const response = await fetch('/api/profile/register/', {
      method: 'POST',
      body: formData
    });
    const result = await response.json();
    if (result.status) {
      alert('Registration successful!');
      location.href = '/dashboard';
    } else {
      alert('Error: ' + result.message);
    }
  };
</script>
```

### Edit Profile Form HTML

```html
<form id="editForm" enctype="multipart/form-data">
  <input type="text" name="full_name" id="fullName">
  <input type="tel" name="contact_no" id="contactNo">
  <input type="password" name="password" placeholder="Leave blank to keep current">
  <input type="file" name="profile_image" accept="image/*">
  <button type="submit">Save Changes</button>
</form>

<script>
  // Load current profile
  const userId = 1;
  fetch(`/api/profile/${userId}/`)
    .then(r => r.json())
    .then(data => {
      document.getElementById('fullName').value = data.data.full_name;
      document.getElementById('contactNo').value = data.data.contact_no;
    });

  // Submit update
  document.getElementById('editForm').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const response = await fetch(`/api/profile/${userId}/update/`, {
      method: 'PUT',
      body: formData
    });
    const result = await response.json();
    if (result.status) {
      alert('Profile updated!');
    } else {
      alert('Error: ' + result.message);
    }
  };
</script>
```

---

## Migration Checklist

From old user management to Profile APIs:

- [ ] Replace registration endpoint with `/api/profile/register/`
- [ ] Update profile retrieval to use `/api/profile/{id}/`
- [ ] Update profile edit endpoint to `/api/profile/{id}/update/`
- [ ] Add image upload to registration form
- [ ] Add image upload to profile edit form
- [ ] Update error message handling
- [ ] Test registration with and without image
- [ ] Test profile retrieval
- [ ] Test profile update (all combinations)
- [ ] Test image replacement (auto-delete old)

---

## API Response Format

All responses follow consistent format:

```json
{
  "status": true/false,
  "message": "Descriptive message",
  "data": { /* response data */ }
}
```

---

**Last Updated:** February 5, 2026
