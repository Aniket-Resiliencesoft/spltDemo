from rest_framework import serializers

from reports.models import ReportExportJob


class ReportExportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportExportJob
        fields = [
            "id",
            "report_type",
            "export_format",
            "status",
            "filters",
            "file_path",
            "message",
            "requested_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "file_path",
            "message",
            "requested_by",
            "created_at",
            "updated_at",
        ]
