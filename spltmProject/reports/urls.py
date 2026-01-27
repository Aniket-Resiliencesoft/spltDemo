from django.urls import path

from reports.api_views.report_api import (
    AdminSummaryReportAPI,
    AdminUsersReportAPI,
    AdminEventsReportAPI,
    AdminPaymentsReportAPI,
    AdminPayoutsReportAPI,
    ReportExportJobListCreateAPI,
    ReportExportJobDetailAPI,
    UserSummaryReportAPI,
    UserEventsReportAPI,
    UserPaymentsReportAPI,
    UserWalletReportAPI,
    UserReceiptAPI,
)
from reports import views as ui_views

urlpatterns = [
    # Admin Reports UI (separated)
    path("reports/admin/", ui_views.admin_reports_collections_page, name="admin_reports_collections_ui"),
    path("reports/admin/collections/", ui_views.admin_reports_collections_page, name="admin_reports_collections_ui"),
    path("reports/admin/events/", ui_views.admin_reports_events_page, name="admin_reports_events_ui"),

    # Admin reports
    path("api/v1/admin/reports/summary/", AdminSummaryReportAPI.as_view()),
    path("api/v1/admin/reports/users/", AdminUsersReportAPI.as_view()),
    path("api/v1/admin/reports/events/", AdminEventsReportAPI.as_view()),
    path("api/v1/admin/reports/payments/", AdminPaymentsReportAPI.as_view()),
    path("api/v1/admin/reports/payouts/", AdminPayoutsReportAPI.as_view()),
    path("api/v1/admin/reports/export/", ReportExportJobListCreateAPI.as_view()),
    path(
        "api/v1/admin/reports/export/<int:job_id>/",
        ReportExportJobDetailAPI.as_view(),
    ),

    # User/app reports
    path("api/v1/reports/me/summary/", UserSummaryReportAPI.as_view()),
    path("api/v1/reports/me/events/", UserEventsReportAPI.as_view()),
    path("api/v1/reports/me/payments/", UserPaymentsReportAPI.as_view()),
    path("api/v1/reports/me/wallet/", UserWalletReportAPI.as_view()),
    path(
        "api/v1/reports/me/receipts/<int:payment_id>/",
        UserReceiptAPI.as_view(),
    ),
]
