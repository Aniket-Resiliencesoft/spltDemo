from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q

from accounts.models import User
from common.decorators import login_required_view
from events.models import Event
from events.utils import parse_event_share_url, calculate_per_person_amount


@login_required_view
def create_event_page(request):
    """Render the create event page with filters and async interactions."""
    return render(request, 'events/create_event.html', {})


@login_required_view
def list_events_page(request):
    """Render the standalone events list page."""
    return render(request, 'events/list_events.html', {})


@login_required_view
def join_event_page(request):
    """
    Handle joining an event via shared URL.
    
    URL Parameters:
        - event_id: Event ID to join
        - amount: Pre-calculated per-person amount
    
    This page displays event details and allows user to confirm joining.
    """
    
    # Get parameters from URL
    event_id = request.GET.get('event_id')
    amount_str = request.GET.get('amount')
    
    # Validate parameters
    validation = parse_event_share_url(event_id, amount_str)
    
    if not validation['is_valid']:
        return render(request, 'events/join_event_error.html', {
            'error': validation['error'],
            'title': 'Invalid Event Link'
        })
    
    # Get event details
    try:
        event = Event.objects.get(id=validation['event_id'])
    except Event.DoesNotExist:
        return render(request, 'events/join_event_error.html', {
            'error': 'Event not found or has been deleted',
            'title': 'Event Not Found'
        })
    
    # Verify event is active
    if event.status not in ['active', 'draft']:
        return render(request, 'events/join_event_error.html', {
            'error': f'This event is {event.get_status_display().lower()} and cannot accept new members',
            'title': 'Event Not Available'
        })
    
    # Prepare context with event details
    context = {
        'event_id': event.id,
        'event_title': event.title,
        'event_description': event.description,
        'event_category': event.get_category_display(),
        'event_date': event.event_date,
        'event_amount': event.event_amount,
        'persons_count': event.persons_count,
        'per_person_amount': validation['per_person_amount'],
        'created_by': event.created_by.full_name,
        'event_location': f"Lat: {event.latitude}, Long: {event.longitude}" if event.latitude and event.longitude else "Not specified",
        'due_pay_date': event.due_pay_date,
    }
    
    return render(request, 'events/join_event.html', context)
