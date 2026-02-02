import json
import hmac
import hashlib

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from payments.models import VendorPaymentTransaction


@csrf_exempt
def razorpay_webhook(request):
    payload = request.body
    received_signature = request.headers.get("X-Razorpay-Signature")

    if not received_signature:
        return HttpResponse(status=400)

    # Verify signature (Razorpay expects HMAC_SHA256(secret, raw_body).hexdigest())
    expected_signature = hmac.new(
        key=bytes(settings.RAZORPAY_WEBHOOK_SECRET, "utf-8"),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, received_signature):
        return HttpResponse(status=400)

    # Parse JSON
    try:
        data = json.loads(payload.decode("utf-8"))
    except Exception:
        return HttpResponse(status=400)

    event = data.get("event", "")
    payout_entity = data.get("payload", {}).get("payout", {}).get("entity", {}) or {}

    payout_id = payout_entity.get("id")
    payout_status = payout_entity.get("status")  # e.g. processing/queued/processed/failed/reversed

    if not payout_id or not payout_status:
        return HttpResponse(status=200)

    # Update DB
    try:
        txn = VendorPaymentTransaction.objects.get(
            razorpay_payout_id=payout_id,
            is_active=True
        )
    except VendorPaymentTransaction.DoesNotExist:
        return HttpResponse(status=200)

    # Optional: if already final, ignore repeats
    # if txn.status in ("processed", "failed", "reversed"):
    #     return HttpResponse(status=200)

    # Store Razorpay status directly
    txn.status = payout_status

    # failure_reason can appear in different fields depending on API/webhook payload
    if payout_status == "failed":
        txn.failure_reason = (
            payout_entity.get("failure_reason")
            or payout_entity.get("status_details", {}).get("description")
            or "Payout failed"
        )
    else:
        txn.failure_reason = ""

    txn.save()

    return HttpResponse(status=200)
