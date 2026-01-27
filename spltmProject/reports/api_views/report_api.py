from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from rest_framework import status

from accounts.models import User
from common.api.base_api import BaseAuthenticatedAPI
from common.responses import api_response_success, api_response_error
from events.models import Event
from payments.models import EventCollectionTransaction
from payments.serializers import (
    EventCollectionTransactionGetSerializer,
    EventCollectionTransactionListSerializer,
)
from reports.models import ReportExportJob
from reports.serializers import ReportExportJobSerializer


# ---------- Helpers ----------

def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _resolve_date_range(request, default_days=365):
    """
    Returns (from_date, to_date) using query params:
    from|fromDate and to|toDate. Defaults to last `default_days`.
    """
    from_val = (
        request.query_params.get("from")
        or request.query_params.get("fromDate")
    )
    to_val = (
        request.query_params.get("to")
        or request.query_params.get("toDate")
    )

    to_date = _parse_date(to_val) or timezone.now().date()
    from_date = _parse_date(from_val) or (to_date - timedelta(days=default_days))

    if from_date > to_date:
        from_date = to_date

    return from_date, to_date


def _get_trunc_fn(interval):
    interval = (interval or "day").lower()
    if interval == "week":
        return TruncWeek, "week"
    if interval == "month":
        return TruncMonth, "month"
    return TruncDate, "day"


def _as_float(value):
    if value is None:
        return 0.0
    return float(value)


# ---------- Admin Reports ----------


class AdminSummaryReportAPI(BaseAuthenticatedAPI):
    """Overall admin dashboard-style summary."""

    def get(self, request):
        # Allow unauthenticated access for dashboard reports (frontend already controls access).
        # If JWT is present middleware will still attach request.jwt_user.
        from_date, to_date = _resolve_date_range(request)
        trunc_cls, interval_label = _get_trunc_fn(request.query_params.get("interval"))

        txn_qs = EventCollectionTransaction.objects.filter(is_active=True)
        txn_qs = txn_qs.filter(
            transaction_date__date__gte=from_date,
            transaction_date__date__lte=to_date,
        )

        completed_total = txn_qs.filter(status="completed").aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")
        pending_total = txn_qs.filter(status="pending").aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")
        failed_count = txn_qs.filter(status="failed").count()

        trunc_field = trunc_cls("transaction_date")
        trend_rows = (
            txn_qs.filter(status="completed")
            .annotate(bucket=trunc_field)
            .values("bucket")
            .annotate(total=Sum("amount"))
            .order_by("bucket")
        )
        collections_trend = [
            {"period": str(row["bucket"]), "amount": _as_float(row["total"])}
            for row in trend_rows
        ]

        events_qs = Event.objects.filter(is_active=True).filter(
            Q(event_date__gte=from_date, event_date__lte=to_date)
            | Q(created_at__date__gte=from_date, created_at__date__lte=to_date)
        )
        event_counts = {
            "total": events_qs.count(),
            "active": events_qs.filter(status="active").count(),
            "completed": events_qs.filter(status="completed").count(),
            "cancelled": events_qs.filter(status="cancelled").count(),
        }

        top_org_rows = (
            events_qs.values(
                "created_by_id",
                "created_by__full_name",
                "created_by__email",
            )
            .annotate(event_count=Count("id"))
            .order_by("-event_count")[:5]
        )
        top_organizers = [
            {
                "user_id": r["created_by_id"],
                "full_name": r["created_by__full_name"],
                "email": r["created_by__email"],
                "events": r["event_count"],
            }
            for r in top_org_rows
        ]

        method_split_rows = (
            txn_qs.values("payment_method")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )
        payment_method_split = [
            {
                "method": r["payment_method"] or "unknown",
                "total": _as_float(r["total"]),
                "count": r["count"],
            }
            for r in method_split_rows
        ]

        data = {
            "range": {
                "from": str(from_date),
                "to": str(to_date),
            },
            "interval": interval_label,
            "collections": {
                "completed_amount": _as_float(completed_total),
                "pending_amount": _as_float(pending_total),
                "failed_count": failed_count,
                "trend": collections_trend,
            },
            "events": event_counts,
            "top_organizers": top_organizers,
            "payment_methods": payment_method_split,
        }

        return self.success_response(
            data=data, message="Admin summary report generated"
        )


class AdminUsersReportAPI(BaseAuthenticatedAPI):
    """Paginated user performance report for admins."""

    def get(self, request):
        # Allow unauthenticated access for demo/report view.
        from_date, to_date = _resolve_date_range(request, default_days=365)
        page_no = int(request.query_params.get("pageNo", 1))
        page_size = int(request.query_params.get("pageSize", 10))
        search = request.query_params.get("search", "").strip()
        status_filter = request.query_params.get("status", "").strip()

        users_qs = User.objects.filter(is_active=True)

        if search:
            users_qs = users_qs.filter(
                Q(full_name__icontains=search)
                | Q(email__icontains=search)
                | Q(contact_no__icontains=search)
            )

        if status_filter:
            try:
                users_qs = users_qs.filter(status=int(status_filter))
            except ValueError:
                pass

        total_count = users_qs.count()
        offset = (page_no - 1) * page_size
        users = users_qs.order_by("-created_at")[offset : offset + page_size]

        data = []
        for user in users:
            user_txn = EventCollectionTransaction.objects.filter(
                user=user, is_active=True
            ).filter(
                transaction_date__date__gte=from_date,
                transaction_date__date__lte=to_date,
            )

            completed_txn = user_txn.filter(status="completed")
            completed_amount = completed_txn.aggregate(total=Sum("amount"))[
                "total"
            ] or Decimal("0.00")

            events_created_qs = Event.objects.filter(
                created_by=user, is_active=True
            ).filter(
                event_date__gte=from_date,
                event_date__lte=to_date,
            )

            last_payment_dt = completed_txn.order_by("-transaction_date").values_list(
                "transaction_date", flat=True
            ).first()

            data.append(
                {
                    "user_id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "contact_no": user.contact_no,
                    "status": user.status,
                    "events_created": events_created_qs.count(),
                    "payments_count": completed_txn.count(),
                    "payments_amount": _as_float(completed_amount),
                    "last_payment_at": last_payment_dt.isoformat() if last_payment_dt else None,
                }
            )

        return self.paginated_response(
            data=data,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
            message="Users report generated",
        )


class AdminEventsReportAPI(BaseAuthenticatedAPI):
    """Event-wise collection report."""

    def get(self, request):
        # Allow dashboard access without forcing JWT (frontend controls visibility).
        from_date, to_date = _resolve_date_range(request, default_days=365)
        page_no = int(request.query_params.get("pageNo", 1))
        page_size = int(request.query_params.get("pageSize", 10))
        status_filter = request.query_params.get("status", "").strip()
        category_filter = request.query_params.get("category", "").strip()
        organizer_id = request.query_params.get("organizer_id")
        search = request.query_params.get("search", "").strip()

        events_qs = Event.objects.filter(is_active=True).filter(
            event_date__gte=from_date,
            event_date__lte=to_date,
        )

        if status_filter:
            events_qs = events_qs.filter(status=status_filter)
        if category_filter:
            events_qs = events_qs.filter(category=category_filter)
        if organizer_id:
            events_qs = events_qs.filter(created_by_id=organizer_id)
        if search:
            events_qs = events_qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        total_count = events_qs.count()
        offset = (page_no - 1) * page_size
        events = events_qs.order_by("-event_date")[offset : offset + page_size]

        data = []
        for event in events:
            event_txn = EventCollectionTransaction.objects.filter(
                event=event, is_active=True
            )
            collected = event_txn.filter(status="completed").aggregate(total=Sum("amount"))[
                "total"
            ] or Decimal("0.00")
            pending = event_txn.filter(status="pending").aggregate(total=Sum("amount"))[
                "total"
            ] or Decimal("0.00")
            participants = (
                event_txn.values("user_id").distinct().count()
            )

            data.append(
                {
                    "event_id": event.id,
                    "title": event.title,
                    "category": event.category,
                    "status": event.status,
                    "event_date": event.event_date,
                    "event_amount": _as_float(event.event_amount),
                    "collected_amount": _as_float(collected),
                    "pending_amount": _as_float(pending),
                    "participants": participants,
                    "organizer_id": event.created_by_id,
                    "organizer_name": getattr(event.created_by, "full_name", ""),
                }
            )

        return self.paginated_response(
            data=data,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
            message="Events report generated",
        )


class AdminPaymentsReportAPI(BaseAuthenticatedAPI):
    """Transaction-level payments report."""

    def get(self, request):
        # Allow unauthenticated access for demo/report view.
        page_no = int(request.query_params.get("pageNo", 1))
        page_size = int(request.query_params.get("pageSize", 10))
        status_filter = request.query_params.get("status", "").strip()
        event_id = request.query_params.get("event_id")
        user_id = request.query_params.get("user_id")
        payment_method = request.query_params.get("payment_method", "").strip()
        from_date, to_date = _resolve_date_range(request, default_days=180)

        txn_qs = EventCollectionTransaction.objects.filter(is_active=True).filter(
            transaction_date__date__gte=from_date,
            transaction_date__date__lte=to_date,
        )

        if status_filter:
            txn_qs = txn_qs.filter(status=status_filter)
        if event_id:
            txn_qs = txn_qs.filter(event_id=event_id)
        if user_id:
            txn_qs = txn_qs.filter(user_id=user_id)
        if payment_method:
            txn_qs = txn_qs.filter(payment_method__iexact=payment_method)

        total_count = txn_qs.count()
        offset = (page_no - 1) * page_size
        transactions = txn_qs.order_by("-transaction_date")[offset : offset + page_size]

        serializer = EventCollectionTransactionListSerializer(transactions, many=True)

        return self.paginated_response(
            data=serializer.data,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
            message="Payments report generated",
        )


class AdminPayoutsReportAPI(BaseAuthenticatedAPI):
    """
    Placeholder payout report. Vendor/payout models are not present
    in the current codebase, so this returns an empty dataset with zero totals.
    """

    def get(self, request):
        err = self.require_admin_role(request)
        if err:
            return err

        data = {
            "total_payouts": 0,
            "pending_payouts": 0,
            "failed_payouts": 0,
            "items": [],
        }
        return self.success_response(
            data=data,
            message="Payout report not available in this build; vendor module missing",
        )


class ReportExportJobListCreateAPI(BaseAuthenticatedAPI):
    """List or queue report exports."""

    def get(self, request):
        err = self.require_admin_role(request)
        if err:
            return err

        page_no = int(request.query_params.get("pageNo", 1))
        page_size = int(request.query_params.get("pageSize", 10))

        qs = ReportExportJob.objects.all()
        total_count = qs.count()
        offset = (page_no - 1) * page_size
        jobs = qs.order_by("-created_at")[offset : offset + page_size]

        serializer = ReportExportJobSerializer(jobs, many=True)
        return self.paginated_response(
            data=serializer.data,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
            message="Export jobs fetched",
        )

    def post(self, request):
        err = self.require_admin_role(request)
        if err:
            return err

        serializer = ReportExportJobSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response_error(
                message="Validation failed",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        job = serializer.save(
            status="pending",
            requested_by_id=request.jwt_user.get("user_id"),
        )

        return api_response_success(
            data=ReportExportJobSerializer(job).data,
            message="Export job created; attach worker to generate file",
            status_code=status.HTTP_201_CREATED,
        )


class ReportExportJobDetailAPI(BaseAuthenticatedAPI):
    """Single export job status."""

    def get(self, request, job_id):
        err = self.require_admin_role(request)
        if err:
            return err

        try:
            job = ReportExportJob.objects.get(id=job_id)
        except ReportExportJob.DoesNotExist:
            return api_response_error(
                message="Export job not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return api_response_success(
            data=ReportExportJobSerializer(job).data,
            message="Export job detail",
        )


# ---------- User (app) Reports ----------


class UserSummaryReportAPI(BaseAuthenticatedAPI):
    """Summary for the authenticated user (organizer/participant)."""

    def get(self, request):
        auth_err = self.require_authentication(request)
        if auth_err:
            return auth_err

        user_id = request.jwt_user.get("user_id")
        from_date, to_date = _resolve_date_range(request, default_days=180)

        created_events = Event.objects.filter(
            created_by_id=user_id,
            is_active=True,
            event_date__gte=from_date,
            event_date__lte=to_date,
        )

        user_txn = EventCollectionTransaction.objects.filter(
            user_id=user_id, is_active=True
        ).filter(
            transaction_date__date__gte=from_date,
            transaction_date__date__lte=to_date,
        )

        paid_amount = user_txn.filter(status="completed").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")
        pending_amount = user_txn.filter(status="pending").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")

        collected_amount = EventCollectionTransaction.objects.filter(
            event__created_by_id=user_id,
            status="completed",
            is_active=True,
            transaction_date__date__gte=from_date,
            transaction_date__date__lte=to_date,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        data = {
            "range": {"from": str(from_date), "to": str(to_date)},
            "events_created": created_events.count(),
            "events_joined": user_txn.values("event_id").distinct().count(),
            "total_paid": _as_float(paid_amount),
            "total_pending": _as_float(pending_amount),
            "total_collected_as_organizer": _as_float(collected_amount),
        }

        return self.success_response(
            data=data, message="User summary report generated"
        )


class UserEventsReportAPI(BaseAuthenticatedAPI):
    """Events for the authenticated user, by role."""

    def get(self, request):
        auth_err = self.require_authentication(request)
        if auth_err:
            return auth_err

        user_id = request.jwt_user.get("user_id")
        role = request.query_params.get("role", "participant").lower()
        page_no = int(request.query_params.get("pageNo", 1))
        page_size = int(request.query_params.get("pageSize", 10))
        from_date, to_date = _resolve_date_range(request, default_days=365)

        events = []
        if role == "organizer":
            base_qs = Event.objects.filter(
                created_by_id=user_id,
                is_active=True,
                event_date__gte=from_date,
                event_date__lte=to_date,
            )
            total_count = base_qs.count()
            offset = (page_no - 1) * page_size
            items = base_qs.order_by("-event_date")[offset : offset + page_size]
            for ev in items:
                collected = EventCollectionTransaction.objects.filter(
                    event=ev, status="completed", is_active=True
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
                events.append(
                    {
                        "event_id": ev.id,
                        "title": ev.title,
                        "status": ev.status,
                        "event_date": ev.event_date,
                        "event_amount": _as_float(ev.event_amount),
                        "collected_amount": _as_float(collected),
                    }
                )
        else:
            base_txn = (
                EventCollectionTransaction.objects.filter(
                    user_id=user_id,
                    is_active=True,
                    transaction_date__date__gte=from_date,
                    transaction_date__date__lte=to_date,
                )
                .values("event_id")
                .distinct()
            )
            event_ids = [row["event_id"] for row in base_txn]
            ev_qs = Event.objects.filter(id__in=event_ids, is_active=True)
            total_count = ev_qs.count()
            offset = (page_no - 1) * page_size
            items = ev_qs.order_by("-event_date")[offset : offset + page_size]
            for ev in items:
                paid = EventCollectionTransaction.objects.filter(
                    event=ev,
                    user_id=user_id,
                    status="completed",
                    is_active=True,
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
                events.append(
                    {
                        "event_id": ev.id,
                        "title": ev.title,
                        "status": ev.status,
                        "event_date": ev.event_date,
                        "amount_paid": _as_float(paid),
                    }
                )

        return self.paginated_response(
            data=events,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
            message="User events report",
        )


class UserPaymentsReportAPI(BaseAuthenticatedAPI):
    """Authenticated user's payment history with filters."""

    def get(self, request):
        auth_err = self.require_authentication(request)
        if auth_err:
            return auth_err

        user_id = request.jwt_user.get("user_id")
        page_no = int(request.query_params.get("pageNo", 1))
        page_size = int(request.query_params.get("pageSize", 10))
        status_filter = request.query_params.get("status", "").strip()
        event_id = request.query_params.get("event_id")
        from_date, to_date = _resolve_date_range(request, default_days=365)

        txn_qs = EventCollectionTransaction.objects.filter(
            user_id=user_id,
            is_active=True,
            transaction_date__date__gte=from_date,
            transaction_date__date__lte=to_date,
        )
        if status_filter:
            txn_qs = txn_qs.filter(status=status_filter)
        if event_id:
            txn_qs = txn_qs.filter(event_id=event_id)

        total_count = txn_qs.count()
        offset = (page_no - 1) * page_size
        transactions = txn_qs.order_by("-transaction_date")[offset : offset + page_size]

        serializer = EventCollectionTransactionListSerializer(transactions, many=True)

        return self.paginated_response(
            data=serializer.data,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
            message="User payments report",
        )


class UserWalletReportAPI(BaseAuthenticatedAPI):
    """Organizer-style wallet view derived from events created by the user."""

    def get(self, request):
        auth_err = self.require_authentication(request)
        if auth_err:
            return auth_err

        user_id = request.jwt_user.get("user_id")
        from_date, to_date = _resolve_date_range(request, default_days=365)

        events_qs = Event.objects.filter(
            created_by_id=user_id,
            is_active=True,
            event_date__gte=from_date,
            event_date__lte=to_date,
        )

        expected_total = events_qs.aggregate(total=Sum("event_amount"))["total"] or Decimal(
            "0.00"
        )
        collected_total = EventCollectionTransaction.objects.filter(
            event__in=events_qs,
            status="completed",
            is_active=True,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        pending_total = expected_total - collected_total
        if pending_total < 0:
            pending_total = Decimal("0.00")

        recent = []
        for ev in events_qs.order_by("-event_date")[:5]:
            collected = EventCollectionTransaction.objects.filter(
                event=ev, status="completed", is_active=True
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            recent.append(
                {
                    "event_id": ev.id,
                    "title": ev.title,
                    "event_date": ev.event_date,
                    "collected_amount": _as_float(collected),
                    "expected_amount": _as_float(ev.event_amount),
                }
            )

        data = {
            "range": {"from": str(from_date), "to": str(to_date)},
            "expected_total": _as_float(expected_total),
            "collected_total": _as_float(collected_total),
            "pending_total": _as_float(pending_total),
            "recent_events": recent,
        }

        return self.success_response(
            data=data, message="Wallet report generated"
        )


class UserReceiptAPI(BaseAuthenticatedAPI):
    """Return receipt-style detail for a single payment belonging to the user."""

    def get(self, request, payment_id):
        auth_err = self.require_authentication(request)
        if auth_err:
            return auth_err

        user_id = request.jwt_user.get("user_id")

        try:
            txn = EventCollectionTransaction.objects.get(
                id=payment_id, user_id=user_id, is_active=True
            )
        except EventCollectionTransaction.DoesNotExist:
            return api_response_error(
                message="Payment not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = EventCollectionTransactionGetSerializer(txn)
        return api_response_success(
            data=serializer.data, message="Payment receipt"
        )
