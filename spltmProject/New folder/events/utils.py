"""
Event URL Generation Utility
Generates shareable URLs for events with calculated per-person amounts
"""

from django.urls import reverse
from decimal import Decimal
from urllib.parse import urlencode


def generate_event_share_url(event, request=None, base_url=None):
    """
    Generate a shareable event URL with event details.
    
    Args:
        event: Event model instance
        request: Django request object (optional, used to get base URL)
        base_url: Custom base URL (optional, overrides request-based URL)
    
    Returns:
        dict: {
            'full_url': 'http://domain.com/join/event/?event_id=123&amount=500.00',
            'relative_url': '/join/event/?event_id=123&amount=500.00',
            'event_id': 123,
            'per_person_amount': Decimal('500.00'),
            'share_link': 'http://domain.com/join/event/?event_id=123&amount=500.00'
        }
    """
    
    # Calculate per-person amount
    if event.persons_count > 0:
        per_person_amount = event.event_amount / Decimal(event.persons_count)
    else:
        per_person_amount = Decimal('0.00')
    
    # Round to 2 decimal places
    per_person_amount = per_person_amount.quantize(Decimal('0.01'))
    
    # Build query parameters
    params = {
        'event_id': event.id,
        'amount': str(per_person_amount),
    }
    
    # Build relative URL
    relative_url = f"/join/event/?{urlencode(params)}"
    
    # Build full URL if request is provided
    full_url = None
    if request:
        full_url = request.build_absolute_uri(relative_url)
    elif base_url:
        full_url = f"{base_url.rstrip('/')}{relative_url}"
    
    return {
        'full_url': full_url,
        'relative_url': relative_url,
        'event_id': event.id,
        'per_person_amount': per_person_amount,
        'share_link': full_url or relative_url,
        'event_title': event.title,
        'event_category': event.get_category_display(),
        'total_amount': event.event_amount,
        'persons_count': event.persons_count,
    }


def generate_event_share_url_short(event_id, per_person_amount, base_url=None):
    """
    Generate a simple shareable URL (without event object dependency).
    Useful for API responses where you only have ID and amount.
    
    Args:
        event_id: Event ID
        per_person_amount: Pre-calculated per-person amount
        base_url: Custom base URL (optional)
    
    Returns:
        str: Shareable URL
    """
    
    params = {
        'event_id': event_id,
        'amount': str(per_person_amount),
    }
    
    relative_url = f"/join/event/?{urlencode(params)}"
    
    if base_url:
        return f"{base_url.rstrip('/')}{relative_url}"
    
    return relative_url


def parse_event_share_url(event_id, amount_str):
    """
    Parse event share URL parameters.
    Used when receiving a shared event link.
    
    Args:
        event_id: Event ID from URL parameter
        amount_str: Per-person amount string from URL parameter
    
    Returns:
        dict: {
            'event_id': int,
            'per_person_amount': Decimal,
            'is_valid': bool,
            'error': str (if not valid)
        }
    """
    
    try:
        event_id = int(event_id)
        amount = Decimal(amount_str)
        
        # Validate amount is positive
        if amount <= 0:
            return {
                'event_id': None,
                'per_person_amount': None,
                'is_valid': False,
                'error': 'Invalid amount: must be greater than 0'
            }
        
        return {
            'event_id': event_id,
            'per_person_amount': amount,
            'is_valid': True,
            'error': None
        }
    
    except (ValueError, TypeError) as e:
        return {
            'event_id': None,
            'per_person_amount': None,
            'is_valid': False,
            'error': f'Invalid URL parameters: {str(e)}'
        }


def calculate_per_person_amount(event_amount, persons_count):
    """
    Calculate per-person amount from event total.
    
    Args:
        event_amount: Total event amount (Decimal or float)
        persons_count: Number of people sharing the cost
    
    Returns:
        Decimal: Per-person amount rounded to 2 decimal places
    """
    
    if persons_count <= 0:
        return Decimal('0.00')
    
    if isinstance(event_amount, float):
        event_amount = Decimal(str(event_amount))
    
    per_person = event_amount / Decimal(persons_count)
    return per_person.quantize(Decimal('0.01'))
