from django.shortcuts import render

from common.decorators import login_required_view


@login_required_view
def admin_reports_collections_page(request):
    """
    Admin UI for total collections (daily/weekly/monthly/custom).
    """
    return render(request, 'reports/admin_reports.html', {})


@login_required_view
def admin_reports_events_page(request):
    """
    Admin UI for event-wise collections with title filter.
    """
    return render(request, 'reports/admin_reports_events.html', {})
