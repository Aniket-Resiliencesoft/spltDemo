from django.db import models


class ReportExportJob(models.Model):
    """
    Lightweight tracker for export requests.
    Actual export generation can be handled asynchronously; this model
    captures intent, filters used, and resulting file metadata.
    """

    REPORT_TYPES = [
        ("summary", "Admin Summary"),
        ("users", "Admin Users"),
        ("events", "Admin Events"),
        ("payments", "Admin Payments"),
        ("payouts", "Admin Payouts"),
        ("user-summary", "User Summary"),
        ("user-events", "User Events"),
        ("user-payments", "User Payments"),
        ("user-wallet", "User Wallet"),
    ]

    STATUSES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    FORMATS = [
        ("csv", "CSV"),
        ("pdf", "PDF"),
        ("json", "JSON"),
    ]

    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    export_format = models.CharField(max_length=10, choices=FORMATS, default="csv")
    status = models.CharField(max_length=20, choices=STATUSES, default="pending")
    filters = models.JSONField(default=dict, blank=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    requested_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_exports",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "report_export_jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.report_type} ({self.export_format}) - {self.status}"
