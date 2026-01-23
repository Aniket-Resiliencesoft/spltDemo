from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q

from accounts.models import User
from common.decorators import login_required_view


@login_required_view
def create_event_page(request):
    """Render the create event page with filters and async interactions."""
    return render(request, 'events/create_event.html', {})


@login_required_view
def list_events_page(request):
    """Render the standalone events list page."""
    return render(request, 'events/list_events.html', {})
