# Quick Start Guide: Wallet-Based Vendor Payments

## Overview

The Wallet-Based Vendor Payment system allows event organizers to pay vendors using their aggregate wallet balance (total collected across all their events) rather than event-specific funds.

---

## 3 Simple APIs

### 1️⃣ Check Wallet Balance

```http
GET /api/organizer/wallet/balance/
Authorization: Bearer {JWT_TOKEN}
```

**What it returns:**
- Total amount collected across all your events
- Current available balance
- Breakdown by event

**Example Response:**
```json
{
  "total_collected": "25000",
  "wallet_balance": "20000",
  "events_breakdown": [
    {
      "event_id": 1,
      "event_title": "Team Outing",
      "amount_collected": "12000"
    }
  ]
}
```

---

### 2️⃣ Create Vendor Payment

```http
POST /api/payments/vendor-wallet/create/
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{
  "event": 1,
  "vendor_name": "ABC Restaurant",
  "vendor_upi": "restaurant@upi",
  "amount": "5000",
  "purpose": "Food charges"
}
```

**Validations:**
- ✅ Amount ≤ Wallet Balance
- ✅ Vendor UPI must contain "@"
- ✅ You must be the event creator

**What it returns:**
- Transaction ID
- Status: "pending"

---

### 3️⃣ Process Payout

```http
POST /api/payments/vendor-wallet/{transaction_id}/payout/
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{}
```

**What it does:**
- Creates Razorpay contact
- Creates fund account
- Initiates UPI payout

**What it returns:**
- Status: "processing"
- Razorpay payout ID (for tracking)

---

## Wallet Balance Formula

```
Wallet Balance = Total Collected - Processing Payouts - Processed Payouts

Example:
  Total Collected (Event 1 + Event 2 + Event 3) = 25,000
  - Processing Payouts (pending at Razorpay)       = 2,000
  - Processed Payouts (already sent to vendors)    = 3,000
  ─────────────────────────────────────────────
  Available Wallet Balance                        = 20,000
```

---

## Rules

| Rule | Details |
|------|---------|
| **Wallet Owner** | Only event creators can use wallet |
| **Spending Limit** | Cannot spend more than available balance |
| **Event Scope** | Can pay vendors for any event you created |
| **Multiple Events** | Wallet includes collections from ALL your events |
| **Payout Status** | Processing payouts reduce available balance |

---

## Common Use Cases

### Scenario 1: Pay Vendor from Multiple Events' Collections

```
You created 3 events:
- Event A: Collected 5000 (from participants)
- Event B: Collected 8000 (from participants)  
- Event C: Collected 7000 (from participants)

Total Wallet = 20000

You want to pay:
- Restaurant (Event A) = 3000 ✅ (20000 - 3000 = 17000 remaining)
- Caterer (Event B) = 5000 ✅ (17000 - 5000 = 12000 remaining)
- Decorator (Event C) = 4000 ✅ (12000 - 4000 = 8000 remaining)

Total spent = 12000
Remaining = 8000
```

### Scenario 2: Insufficient Balance

```
Your wallet balance = 5000

You try to pay vendor 6000 ❌

Error Response:
{
  "message": "Insufficient wallet balance",
  "wallet_balance": "5000",
  "requested_amount": "6000"
}
```

---

## Status Tracking

### During Creation
```
Status: "pending"
Meaning: Transaction created, awaiting payout initiation
```

### During Payout
```
Status: "processing"
Meaning: Razorpay is processing the UPI transfer
Razorpay Payout ID: pout_xxxxx (use for tracking)
```

### After Completion
```
Status: "processed"
Meaning: Money successfully transferred to vendor
```

### If Failed
```
Status: "failed"
Failure Reason: "Invalid UPI" | "Insufficient balance" etc.
```

---

## cURL Examples

### Get Balance
```bash
curl -X GET https://your-api.com/api/organizer/wallet/balance/ \
  -H "Authorization: Bearer eyJhbGc..."
```

### Create Payment
```bash
curl -X POST https://your-api.com/api/payments/vendor-wallet/create/ \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "event": 1,
    "vendor_name": "Vendor Name",
    "vendor_upi": "vendor@upi",
    "amount": "1000",
    "purpose": "Service charge"
  }'
```

### Initiate Payout
```bash
curl -X POST https://your-api.com/api/payments/vendor-wallet/5/payout/ \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Insufficient wallet balance" | Check `/api/organizer/wallet/balance/` to see available funds |
| "Payout already initiated" | The transaction was already processed, check status |
| "Invalid UPI" | Ensure vendor UPI format is correct (e.g., name@upi) |
| "Event not found" | Verify the event ID exists and you are the creator |
| "Not authenticated" | Include valid JWT token in Authorization header |

---

## Key Differences from Old APIs

### Previous API (Event-Based)
- Endpoint: `/api/payments/vendor/create/`
- Limit: Can only spend event's collected amount
- Scope: Single event validation

### New API (Wallet-Based)
- Endpoint: `/api/payments/vendor-wallet/create/`
- Limit: Can spend total wallet balance across all events
- Scope: Organizer-wide validation
- **Better for:** Flexible organizer spending

---

## Implementation Checklist

- [ ] Replace old vendor payment endpoints with wallet-based in frontend
- [ ] Update payment creation form to show wallet balance
- [ ] Display event breakdown in wallet view
- [ ] Show available balance before creating payment
- [ ] Implement error handling for insufficient balance
- [ ] Track payout status with Razorpay ID
- [ ] Test with multiple events

---

## Support

For issues or questions:
1. Check wallet balance endpoint for current status
2. Verify event creator permissions
3. Ensure vendor UPI format is valid
4. Review transaction status after creation

---

**Last Updated:** February 5, 2026
