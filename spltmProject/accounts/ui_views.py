from decimal import Decimal

from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.utils import OperationalError, ProgrammingError
from django.db.models.functions import TruncMonth

from accounts.models import User
from events.models import Event
from payments.models import EventCollectionTransaction

def login_view(request):
    """
    Renders login page.
    """
    return render(request, 'auth/login.html')

def adminDashBoard(request):
    """
    Docstring for adminDashBoard
    
    :param request: Description
    """
    # Default context (avoids crashes if migrations not applied)
    context = {
        'total_users': 0,
        'total_events': 0,
        'collected_amount': Decimal('0'),
        'pending_payouts': Decimal('0'),
        'monthly_labels': [],
        'monthly_amounts': [],
        'event_status_labels': [],
        'event_status_counts': [],
        'recent_events': [],
    }

    try:
        # Aggregate dashboard metrics
        context['total_users'] = User.objects.filter(is_active=True).count()
        context['total_events'] = Event.objects.filter(is_active=True).count()

        txn_qs = EventCollectionTransaction.objects.filter(is_active=True)
        context['collected_amount'] = txn_qs.filter(status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        context['pending_payouts'] = txn_qs.filter(status='pending').aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Monthly collection chart (completed transactions by month, current year)
        monthly = (
            txn_qs.filter(status='completed')
            .annotate(month=TruncMonth('transaction_date'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )
        context['monthly_labels'] = [
            m['month'].strftime('%b') if m['month'] else '' for m in monthly
        ]
        context['monthly_amounts'] = [
            float(m['total']) if m['total'] else 0 for m in monthly
        ]

        # Event status counts
        status_counts = (
            Event.objects.filter(is_active=True)
            .values('status')
            .annotate(count=Count('id'))
        )
        context['event_status_labels'] = [sc['status'] for sc in status_counts]
        context['event_status_counts'] = [sc['count'] for sc in status_counts]

        # Recent events
        recent = Event.objects.filter(is_active=True).order_by('-created_at')[:5]
        context['recent_events'] = [
            {
                'title': ev.title,
                'organizer': getattr(ev.created_by, 'full_name', ''),
                'amount': '',  # placeholder; fill when event amount exists
                'status': ev.get_status_display(),
                'status_raw': ev.status,
            }
            for ev in recent
        ]
    except (OperationalError, ProgrammingError):
        # Likely migrations missing; keep defaults and let page render
        pass

    return render(request, 'splitmoneyDashBoard.html', context)
