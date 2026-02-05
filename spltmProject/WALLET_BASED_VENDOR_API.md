# Wallet-Based Vendor Payment APIs

## Overview

The Wallet-Based Vendor Payment APIs allow organizers to manage vendor payments using their total wallet balance across all events they created, rather than being restricted to a single event's collection.

**Key Concept:** An organizer's wallet is the sum of all money collected across all events they have created. They can spend up to this balance regardless of which specific event they're paying for.

---

## API Endpoints

### 1. Create Vendor Payment (Wallet-Based)

Creates a new vendor payment transaction with wallet balance validation.

#### Request

```
POST /api/payments/vendor-wallet/create/
```

**Authentication:** Required (JWT Token in Authorization header)

**Content-Type:** `application/json`

#### Payload

```json
{
  "event": 1,
  "vendor_name": "ABC Restaurant",
  "vendor_upi": "restaurant@upi",
  "amount": "5000",
  "purpose": "Food service charges"
}
```

#### Payload Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event` | integer | Yes | Event ID for which vendor payment is being created |
| `vendor_name` | string | Yes | Name of the vendor |
| `vendor_upi` | string | Yes | UPI address of vendor (must contain @) |
| `amount` | decimal/string | Yes | Amount to pay to vendor |
| `purpose` | string | No | Reason/purpose of payment |

#### Success Response (201 Created)

```json
{
  "status": true,
  "message": "Vendor payment created (wallet-based)",
  "data": {
    "id": 5,
    "event": 1,
    "vendor_name": "ABC Restaurant",
    "vendor_upi": "restaurant@upi",
    "amount": "5000.00",
    "purpose": "Food service charges",
    "status": "pending",
    "initiated_by": 1,
    "created_at": "2026-02-05T10:30:00Z",
    "updated_at": "2026-02-05T10:30:00Z"
  }
}
```

#### Error Response (400 - Insufficient Wallet)

```json
{
  "status": false,
  "message": "Insufficient wallet balance",
  "data": {
    "total_collected": "8000",
    "processing_payouts": "2000",
    "processed_payouts": "1000",
    "wallet_balance": "5000",
    "requested_amount": "6000"
  }
}
```

#### Error Response (403 - Not Event Creator)

```json
{
  "status": false,
  "message": "Only the event organiser can create vendor payments",
  "statusCode": 403
}
```

#### Error Response (404 - Event Not Found)

```json
{
  "status": false,
  "message": "Event not found",
  "statusCode": 404
}
```

#### Validation Rules

- ✅ User must be the creator of the event
- ✅ Requested amount must NOT exceed organizer's wallet balance
- ✅ Vendor UPI must contain "@"
- ✅ Vendor name must not be empty
- ✅ Event must exist and be active

---

### 2. Initiate Payout (Wallet-Based)

Triggers the Razorpay payout for a wallet-based vendor payment transaction.

#### Request

```
POST /api/payments/vendor-wallet/<transaction_id>/payout/
```

**Authentication:** Required (JWT Token)

**Content-Type:** `application/json`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `transaction_id` | integer | Yes | Vendor payment transaction ID |

#### Payload

```json
{}
```

(Empty body - all data comes from the transaction record)

#### Success Response (200 OK)

```json
{
  "status": true,
  "message": "Vendor payout initiated (wallet-based)",
  "data": {
    "id": 5,
    "event": 1,
    "vendor_name": "ABC Restaurant",
    "vendor_upi": "restaurant@upi",
    "amount": "5000.00",
    "purpose": "Food service charges",
    "status": "processing",
    "razorpay_payout_id": "pout_HO2jzHWj8Bzbkw",
    "razorpay_contact_id": "cont_HO2jzHWj8Bzbkw",
    "razorpay_fund_account_id": "fa_HO2jzHWj8Bzbkw",
    "failure_reason": "",
    "updated_at": "2026-02-05T10:35:00Z"
  }
}
```

#### Error Response (400 - Payout Already Initiated)

```json
{
  "status": false,
  "message": "Payout already initiated",
  "statusCode": 400
}
```

#### Error Response (400 - Invalid UPI)

```json
{
  "status": false,
  "message": "Invalid or missing vendor UPI",
  "data": {
    "vendor_upi": "restaurant-upi"
  },
  "statusCode": 400
}
```

#### Error Response (404 - Transaction Not Found)

```json
{
  "status": false,
  "message": "Transaction not found",
  "statusCode": 404
}
```

#### Error Response (500 - Razorpay Config Missing)

```json
{
  "status": false,
  "message": "RAZORPAY_ACCOUNT_NUMBER not configured",
  "statusCode": 500
}
```

#### Validation Rules

- ✅ Transaction must exist and be active
- ✅ Payout should not be already initiated
- ✅ Vendor name must not be empty
- ✅ Vendor UPI must be valid (contain @)
- ✅ Amount must be greater than 0
- ✅ Razorpay account number must be configured

---

### 3. Get Organizer Wallet Balance

Retrieves the organizer's total wallet balance and breakdown by event.

#### Request

```
GET /api/organizer/wallet/balance/
```

**Authentication:** Required (JWT Token)

**Content-Type:** `application/json`

#### Path Parameters

None

#### Query Parameters

None

#### Payload

None (GET request)

#### Success Response (200 OK)

```json
{
  "status": true,
  "message": "Organizer wallet balance retrieved",
  "data": {
    "organizer_id": 1,
    "total_collected": "25000.00",
    "processing_payouts": "5000.00",
    "processed_payouts": "10000.00",
    "wallet_balance": "10000.00",
    "event_count": 3,
    "events_breakdown": [
      {
        "event_id": 1,
        "event_title": "Team Outing",
        "amount_collected": "12000.00"
      },
      {
        "event_id": 2,
        "event_title": "Office Party",
        "amount_collected": "8000.00"
      },
      {
        "event_id": 3,
        "event_title": "Team Lunch",
        "amount_collected": "5000.00"
      }
    ]
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `organizer_id` | integer | ID of the authenticated organizer |
| `total_collected` | decimal | Total amount collected across ALL events created by organizer |
| `processing_payouts` | decimal | Total amount in "processing" payout status |
| `processed_payouts` | decimal | Total amount with "processed" status |
| `wallet_balance` | decimal | Available balance = total_collected - processing_payouts - processed_payouts |
| `event_count` | integer | Number of active events created by organizer |
| `events_breakdown` | array | Per-event collection breakdown |

#### Error Response (401 - Not Authenticated)

```json
{
  "status": false,
  "message": "Authentication required",
  "statusCode": 401
}
```

---

## Wallet Balance Calculation

```
Wallet Balance = Total Collected - Processing Payouts - Processed Payouts

Where:
  Total Collected = Sum of all completed transactions across ALL organizer's events
  Processing Payouts = Sum of vendor payouts with status = "processing"
  Processed Payouts = Sum of vendor payouts with status = "processed"
```

### Example Scenario

```
Event 1 Collections:
  - User A paid 5000
  - User B paid 3000
  Total: 8000

Event 2 Collections:
  - User A paid 4000
  - User C paid 5000
  Total: 9000

Event 3 Collections:
  - User B paid 2000
  - User D paid 6000
  Total: 8000

TOTAL COLLECTED = 8000 + 9000 + 8000 = 25000

Vendor Payouts:
  - Payout 1 (Event 1): 2000 [status: processing]
  - Payout 2 (Event 2): 3000 [status: processed]

PROCESSING = 2000
PROCESSED = 3000

WALLET BALANCE = 25000 - 2000 - 3000 = 20000

Organizer can spend up to 20000 regardless of which event they choose!
```

---

## Workflow

### Step 1: Check Wallet Balance
```bash
curl -X GET \
  http://localhost:8000/api/organizer/wallet/balance/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Step 2: Create Vendor Payment (Wallet-Based)
```bash
curl -X POST \
  http://localhost:8000/api/payments/vendor-wallet/create/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event": 1,
    "vendor_name": "ABC Restaurant",
    "vendor_upi": "restaurant@upi",
    "amount": "5000",
    "purpose": "Food charges"
  }'
```

### Step 3: Initiate Payout
```bash
curl -X POST \
  http://localhost:8000/api/payments/vendor-wallet/5/payout/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Comparison: Event-Based vs Wallet-Based APIs

| Aspect | Event-Based API | Wallet-Based API |
|--------|-----------------|------------------|
| **Endpoint** | `/api/payments/vendor/create/` | `/api/payments/vendor-wallet/create/` |
| **Validation** | Event-specific collected amount | Organizer's total wallet across ALL events |
| **Spending Limit** | Limited by single event collections | Limited by total wallet balance |
| **Use Case** | Pay vendors for specific event | Flexible organizer spending |
| **Balance Calculation** | Single event total | All events total - all payouts |

---

## Status Transitions

```
Payment Status Flow:
pending → processing → processed ✓
   ↓
  failed ✗
```

### Status Meanings

- **pending**: Transaction created, waiting for payout initiation
- **processing**: Payout initiated with Razorpay, awaiting completion
- **processed**: Successfully paid to vendor
- **failed**: Payout failed (see failure_reason field)

---

## Error Codes

| Code | Meaning | Example |
|------|---------|---------|
| 201 | Created | Vendor payment successfully created |
| 200 | OK | Payout initiated / Balance retrieved |
| 400 | Bad Request | Invalid input, insufficient balance, payout already initiated |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Not the event creator |
| 404 | Not Found | Transaction/Event not found |
| 500 | Internal Server Error | Razorpay config missing or API error |

---

## Authentication

All endpoints require JWT authentication via Bearer token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Rate Limits

No specific rate limits defined. Standard Django/DRF rate limiting applies if configured.

---

## Sandbox Testing

For testing in sandbox mode, use test Razorpay credentials:
- **Key ID**: `rzp_test_SA1lNy5jZQ6Mrb`
- **Key Secret**: `Ye43th4C2v57hOd5RTjFkilb`

---

## Notes

- All amounts are in INR currency
- Decimal precision: 2 places
- Dates are in ISO 8601 format (UTC)
- Only event creator can manage vendor payments
- Wallet balance includes all active events
- Payouts in "failed" or "reversed" status don't affect balance calculations
