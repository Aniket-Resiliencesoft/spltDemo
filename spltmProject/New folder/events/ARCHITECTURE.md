"""
Event Model Architecture & Data Flow

Visual representation of Event model relationships and API flow
"""

# ============ Database Relationships ============

"""
┌─────────────────────────────┐
│          User               │
│  (accounts/models.py)       │
├─────────────────────────────┤
│ • id (PK)                   │
│ • email                     │
│ • password_hash             │
│ • created_at                │
│ • updated_at                │
│ • is_active                 │
└────────────────┬────────────┘
                 │ 1:Many
                 │ created_by
                 │
                 ▼
┌─────────────────────────────────────┐
│          Event                      │
│  (events/models.py)                 │
├─────────────────────────────────────┤
│ • id (PK)                           │
│ • title                             │
│ • category ◄──────────────┐         │
│ • description             │         │
│ • event_date              │         │
│ • start_date_time         │         │
│ • end_date_time           │         │
│ • latitude                │         │
│ • longitude               │         │
│ • due_pay_date            │         │
│ • persons_count           │         │
│ • status ◄────────────┐   │         │
│ • created_by (FK)     │   │         │
│ • created_at          │   │         │
│ • updated_at          │   │         │
│ • is_active           │   │         │
└───────────────────────┼───┼─────────┘
                        │   │
        ┌───────────────┘   │
        │                   │
    Categories         Statuses
    ┌─────────────────┐┌─────────────────┐
    │ • turf          ││ • draft         │
    │ • restaurant    ││ • active        │
    │ • trip          ││ • closed        │
    │ • party         ││ • completed     │
    │ • custom        ││ • cancelled     │
    └─────────────────┘└─────────────────┘
"""

# ============ API Request/Response Flow ============

"""
CLIENT REQUEST
    │
    ├─→ Authorization Header: Bearer <JWT_TOKEN>
    │       ▼
    │   JWTAuthenticationMiddleware
    │   (common/middleware/jwt_auth_middleware.py)
    │       ▼
    │   request.jwt_user = {
    │       'user_id': 1,
    │       'username': 'user@email.com',
    │       'role': 'ADMIN' or null,
    │       'exp': ...,
    │       'iat': ...
    │   }
    │
    └─→ API View
            │
            ├─→ BaseAuthenticatedAPI
            │   (common/api/base_api.py)
            │       │
            │       ├─→ require_authentication()
            │       │   ✓ Check if jwt_user exists
            │       │   ✗ Return 401
            │       │
            │       ├─→ require_admin_role()
            │       │   ✓ Check role == 'ADMIN'
            │       │   ✗ Return 403
            │       │
            │       └─→ require_self_or_admin()
            │           ✓ Check creator or admin
            │           ✗ Return 403
            │
            ├─→ Serializer Validation
            │   (events/serializers.py)
            │       ├─→ EventCreateSerializer
            │       ├─→ EventUpdateSerializer
            │       └─→ EventListSerializer
            │
            ├─→ Database Query
            │   ├─→ Event.objects.filter(is_active=True)
            │   └─→ Use indexes for optimization
            │
            └─→ Response
                ├─→ success_response()
                ├─→ error_response()
                └─→ paginated_response()
                    (common/responses.py)
                        ▼
                    APIResponse.to_dict()
                        ▼
                    {
                        "IsSuccess": true/false,
                        "Message": "...",
                        "Data": [...],
                        "PageNo": 1,    (optional)
                        "PageSize": 10  (optional)
                    }
                        ▼
                    CLIENT RESPONSE
"""

# ============ Event Lifecycle (Status Transitions) ============

"""
┌──────────┐
│  Draft   │  ← Initial state when created
└────┬─────┘
     │
     ├─→ Can edit all fields
     │   • title
     │   • category
     │   • dates
     │   • location
     │   • person count
     │
     └─→ User initiates event
         (e.g., "Let's plan a trip")
         │
         ▼
     ┌──────────┐
     │  Active  │  ← Event is live
     └────┬─────┘
          │
          ├─→ Can edit some fields
          │   • description only
          │
          ├─→ Participants join
          ├─→ Expenses are added
          │
          └─→ Event ends (date passes)
              │
              ▼
          ┌──────────┐
          │  Closed  │  ← No more expenses
          └────┬─────┘
               │
               ├─→ No edits allowed
               │
               ├─→ Payments being settled
               │
               └─→ All paid up
                   │
                   ▼
               ┌──────────────┐
               │  Completed   │  ← Final state
               └──────────────┘

Alternative: Any state → Cancelled
              (Event cancelled by creator/admin)
              └──────────────┐
                             ▼
                       ┌───────────────┐
                       │  Cancelled    │
                       └───────────────┘
"""

# ============ API Endpoint Mapping ============

"""
REQUEST METHOD  │  ENDPOINT              │  API VIEW
────────────────┼────────────────────────┼──────────────────────
GET             │ /api/events/           │ EventListAPI
                │                        │ • Pagination
                │                        │ • Filtering by status/category
                │                        │ • Returns 10 per page (default)
────────────────┼────────────────────────┼──────────────────────
POST            │ /api/events/create/    │ EventCreateAPI
                │                        │ • Create new event
                │                        │ • Set created_by = current user
                │                        │ • Returns 201 Created
────────────────┼────────────────────────┼──────────────────────
GET             │ /api/events/<id>/      │ EventDetailAPI
                │                        │ • Get full event details
                │                        │ • Includes all fields
────────────────┼────────────────────────┼──────────────────────
PUT/PATCH       │ /api/events/<id>/      │ EventUpdateAPI
                │ update/                │ • Update event fields
                │                        │ • PUT: all fields
                │                        │ • PATCH: partial
                │                        │ • Auth: creator/admin only
────────────────┼────────────────────────┼──────────────────────
PATCH           │ /api/events/<id>/      │ EventStatusUpdateAPI
                │ status/                │ • Update status only
                │                        │ • Validates transitions
                │                        │ • Auth: creator/admin only
────────────────┼────────────────────────┼──────────────────────
DELETE          │ /api/events/<id>/      │ EventDeleteAPI
                │ delete/                │ • Soft delete (is_active=False)
                │                        │ • Data remains in DB
                │                        │ • Auth: creator/admin only
"""

# ============ Authorization Decision Tree ============

"""
Request arrives
    │
    ▼
Is Authorization header present?
    │
    ├─ NO ──→ Check for auth cookie
    │         │
    │         ├─ NO COOKIE ──→ NO jwt_user ──→ CONTINUE (public view)
    │         │
    │         └─ COOKIE ──→ Decode JWT ──→ SET jwt_user
    │
    └─ YES ──→ Format: "Bearer <token>"?
              │
              ├─ NO ──→ Return 401 "Invalid header format"
              │
              └─ YES ──→ Decode JWT
                        │
                        ├─ VALID ──→ SET jwt_user
                        │
                        └─ INVALID/EXPIRED ──→ Return 401


API View checks:
    │
    ├─→ require_authentication()
    │   if not jwt_user → Return 401
    │
    ├─→ require_admin_role()
    │   if jwt_user.role != 'ADMIN' → Return 403
    │
    └─→ require_self_or_admin(event.created_by_id)
        if jwt_user.user_id != created_by_id
        and jwt_user.role != 'ADMIN' → Return 403


Grant Access ✓
"""

# ============ Database Query Optimization ============

"""
Indexes created:
1. (status, event_date)
   → Optimizes: SELECT * FROM events WHERE status='active' ORDER BY event_date
   → Used in: EventListAPI with status filter
   → Query type: Range + Sort

2. (created_by_id, status)
   → Optimizes: SELECT * FROM events WHERE created_by=? AND status='active'
   → Used in: Filter by creator + status
   → Query type: Composite lookup

Without indexes: Full table scan (slow)
With indexes:   Index lookup (fast)
"""

# ============ Error Response Examples ============

"""
401 Unauthorized (No Token):
{
  "IsSuccess": false,
  "Message": "Authentication required",
  "Data": null
}

401 Unauthorized (Invalid Token):
{
  "IsSuccess": false,
  "Message": "Invalid token",
  "Data": null
}

403 Forbidden (Not Creator/Admin):
{
  "IsSuccess": false,
  "Message": "Permission denied",
  "Data": null
}

404 Not Found:
{
  "IsSuccess": false,
  "Message": "Event not found",
  "Data": null
}

400 Bad Request (Validation):
{
  "IsSuccess": false,
  "Message": "Validation failed",
  "Data": {
    "title": ["This field may not be blank."],
    "start_date_time": ["Start datetime must be before end datetime."]
  }
}

201 Created (Success):
{
  "IsSuccess": true,
  "Message": "Event created successfully",
  "Data": {
    "id": 1,
    "title": "...",
    ...
  }
}
"""
