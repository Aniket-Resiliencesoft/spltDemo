"""
Event URL Generation Utility
Generates shareable URLs for events with calculated per-person amounts
"""

from django.urls import reverse
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode


def compute_split(total_amount, total_members, admin_percentage=Decimal('5.5')):
    """Compute base share, admin charge, final per-head and totals using Decimal.

    Returns a dict with:
      - per_head
      - admin_charge_per_head
      - final_per_head
      - total_admin_amount
      - total_collected (final_per_head * total_members)

    All values are Decimal quantized to 2 decimal places (ROUND_HALF_UP).
    """
    # Normalize inputs
    if isinstance(total_amount, float):
        total_amount = Decimal(str(total_amount))
    else:
        total_amount = Decimal(total_amount)

    if isinstance(total_members, int):
        total_members = int(total_members)

    admin_percentage = Decimal(str(admin_percentage))

    TWO = Decimal('0.01')

    if total_members <= 0:
        zero = Decimal('0.00')
        return {
            'per_head': zero,
            'admin_charge_per_head': zero,
            'final_per_head': zero,
            'total_admin_amount': zero,
            'total_collected': zero,
        }

    # Base per-head (what goes to the event wallet)
    per_head = (total_amount / Decimal(total_members)).quantize(TWO, rounding=ROUND_HALF_UP)

    # Admin charge per head (percentage of base per-head)
    admin_charge_per_head = ((per_head * admin_percentage) / Decimal('100')).quantize(TWO, rounding=ROUND_HALF_UP)

    # Final amount each member pays
    final_per_head = (per_head + admin_charge_per_head).quantize(TWO, rounding=ROUND_HALF_UP)

    # Totals
    total_admin_amount = (admin_charge_per_head * Decimal(total_members)).quantize(TWO, rounding=ROUND_HALF_UP)
    total_collected = (final_per_head * Decimal(total_members)).quantize(TWO, rounding=ROUND_HALF_UP)

    return {
        'per_head': per_head,
        'admin_charge_per_head': admin_charge_per_head,
        'final_per_head': final_per_head,
        'total_admin_amount': total_admin_amount,
        'total_collected': total_collected,
    }


def generate_event_share_url(
    event,
    request=None,
    base_url=None,
    deeplink_base_url=None,
    admin_percentage=Decimal('5.5')
):
    """
    Generate a shareable event URL (supports normal web + App deep links).

    The `amount` parameter in the URL is the final per-head amount (including admin charge).
    The utility also returns detailed split values.
    """

    split = compute_split(event.event_amount, event.persons_count, admin_percentage=admin_percentage)

    params = {
        'event_id': event.id,
        'amount': str(split['final_per_head']),
    }

    relative_url = f"/join/event/?{urlencode(params)}"

    full_url = None
    if deeplink_base_url:
        full_url = f"{deeplink_base_url.rstrip('/')}{relative_url}"
    elif request:
        full_url = request.build_absolute_uri(relative_url)
    elif base_url:
        full_url = f"{base_url.rstrip('/')}{relative_url}"

    return {
        'full_url': full_url,
        'relative_url': relative_url,
        'event_id': event.id,
        'per_person_amount': split['final_per_head'],
        'base_per_person': split['per_head'],
        'admin_charge_per_head': split['admin_charge_per_head'],
        'total_admin_amount': split['total_admin_amount'],
        'total_amount': event.event_amount,
        'total_collected': split['total_collected'],
        'share_link': full_url or relative_url,
        'event_title': event.title,
        'event_category': event.category,
        'persons_count': event.persons_count,
    }


def generate_event_share_url_short(event_id, per_person_amount, base_url=None):
    """
    Generate a simple shareable URL (without event object dependency).
    `per_person_amount` should be a Decimal or string representation of the final per-head amount.
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
    Returns final per-person amount as Decimal when valid.
    """
    try:
        event_id = int(event_id)
        amount = Decimal(amount_str)

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


def calculate_per_person_amount(event_amount, persons_count, admin_percentage=Decimal('5.5')):
    """
    Calculate per-person amounts and return the final per-head (including admin charge) as Decimal.
    """
    split = compute_split(event_amount, persons_count, admin_percentage=admin_percentage)
    return split['final_per_head']
