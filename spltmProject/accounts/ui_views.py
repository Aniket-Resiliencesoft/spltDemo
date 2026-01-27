from decimal import Decimal
import hashlib
import json
import time

from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.db.models import Sum, Count
from django.db.utils import OperationalError, ProgrammingError
from django.db.models.functions import TruncMonth
from django.http import StreamingHttpResponse, HttpResponse

from accounts.models import User
from events.models import Event
from payments.models import EventCollectionTransaction
from common.decorators import login_required_view
from common.utils.jwt_utils import decode_jwt_token

def login_view(request):
    """
    Renders login page.
    If user is already logged in with a VALID token, redirects to dashboard.
    If token is invalid/expired, clears it and shows login page.
    """
    token = request.COOKIES.get('access_token')
    
    if token:
        # Validate token before redirecting
        try:
            payload = decode_jwt_token(token)
            # Token is valid, redirect to dashboard
            return redirect('/dashboard/')
        except Exception as e:
            # Token is invalid or expired
            # Clear the invalid token and show login page
            response = render(request, 'auth/login.html')
            response.delete_cookie('access_token')
            return response
    
    # No token, show login page
    return render(request, 'auth/login.html')


def register_view(request):
    """
    Renders registration page.
    If user is already logged in with a VALID token, redirects to dashboard.
    """
    token = request.COOKIES.get('access_token')
    
    if token:
        # Validate token before redirecting
        try:
            payload = decode_jwt_token(token)
            # Token is valid, redirect to dashboard
            return redirect('/dashboard/')
        except Exception as e:
            # Token is invalid or expired
            # Clear the invalid token and show registration page
            response = render(request, 'auth/register.html')
            response.delete_cookie('access_token')
            return response
    
    # No token, show registration page
    return render(request, 'auth/register.html')


def verify_otp_view(request):
    """
    Renders OTP verification page for non-admin users.
    Expects otp_user_id and otp_email to be set in localStorage on client side.
    """
    # Check if user has been redirected from login
    # This is client-side validation, so we just render the page
    return render(request, 'auth/verify_otp.html')


@login_required_view
def dashboard_view(request):
    """
    Renders dashboard page for authenticated users.
    Shows statistics about users, events, and payments.
    """
    return render(request, 'dashboard.html')


@login_required_view
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

    return render(request, 'adminDashBoard.html', context)


@login_required_view
def dashboard_stream(request):
    """
    Server-Sent Events endpoint that pushes dashboard snapshots when data changes.
    """
    # Basic auth guard: allow if no role is set (legacy token) or ADMIN
    # jwt_user = getattr(request, 'jwt_user', None)
    # role = jwt_user.get('role') if jwt_user else None
    # if jwt_user is None:
    #     return HttpResponse("Unauthorized", status=401)
    # if role and str(role).upper() != 'ADMIN':
    #     return HttpResponse("Forbidden", status=403)

    def snapshot():
        data = {
            'users': [],
            'events': [],
            'payments': [],
            'totals': {
                'users': 0,
                'events': 0,
                'collected': 0,
                'pending': 0,
            },
            'charts': {
                'monthly_labels': [],
                'monthly_amounts': [],
                'status_labels': [],
                'status_counts': [],
            }
        }
        try:
            # Users
            users_qs = User.objects.filter(is_active=True).order_by('-created_at')[:100]
            data['users'] = [
                {
                    'id': u.id,
                    'full_name': u.full_name,
                    'email': u.email,
                    'contact_no': u.contact_no,
                    'status': u.status,
                } for u in users_qs
            ]
            data['totals']['users'] = users_qs.count()

            # Events
            events_qs = Event.objects.filter(is_active=True).select_related('created_by').order_by('-created_at')[:100]
            data['events'] = [
                {
                    'id': ev.id,
                    'title': ev.title,
                    'category': ev.category,
                    'category_display': ev.get_category_display(),
                    'event_date': ev.event_date,
                    'start_date_time': ev.start_date_time,
                    'end_date_time': ev.end_date_time,
                    'due_pay_date': ev.due_pay_date,
                    'persons_count': ev.persons_count,
                    'status': ev.status,
                    'status_display': ev.get_status_display(),
                    'created_by_name': getattr(ev.created_by, 'full_name', ''),
                }
                for ev in events_qs
            ]
            data['totals']['events'] = events_qs.count()

            # Payments / transactions
            txn_qs = EventCollectionTransaction.objects.filter(is_active=True)
            data['payments'] = [
                {
                    'id': tx.id,
                    'event_title': getattr(tx.event, 'title', ''),
                    'user_name': getattr(tx.user, 'full_name', ''),
                    'amount': float(tx.amount),
                    'status': tx.status,
                    'status_display': tx.get_status_display(),
                    'transaction_date': tx.transaction_date,
                }
                for tx in txn_qs[:100]
            ]
            data['totals']['collected'] = float(txn_qs.filter(status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0'))
            data['totals']['pending'] = float(txn_qs.filter(status='pending').aggregate(total=Sum('amount'))['total'] or Decimal('0'))

            monthly = (
                txn_qs.filter(status='completed')
                .annotate(month=TruncMonth('transaction_date'))
                .values('month')
                .annotate(total=Sum('amount'))
                .order_by('month')
            )
            data['charts']['monthly_labels'] = [
                m['month'].strftime('%b') if m['month'] else '' for m in monthly
            ]
            data['charts']['monthly_amounts'] = [
                float(m['total']) if m['total'] else 0 for m in monthly
            ]

            status_counts = (
                Event.objects.filter(is_active=True)
                .values('status')
                .annotate(count=Count('id'))
            )
            data['charts']['status_labels'] = [sc['status'] for sc in status_counts]
            data['charts']['status_counts'] = [sc['count'] for sc in status_counts]

        except (OperationalError, ProgrammingError):
            pass
        return data

    def event_stream():
        last_sig = None
        idle = 0
        while True:
            payload = snapshot()
            sig = hashlib.md5(json.dumps(payload, default=str, sort_keys=True).encode()).hexdigest()
            if sig != last_sig:
                last_sig = sig
                idle = 0
                yield f"data: {json.dumps(payload, default=str)}\n\n"
            else:
                idle += 1
                if idle % 10 == 0:
                    yield "event: ping\ndata: {}\n\n"
            time.sleep(2)

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@login_required_view
def user_list_view(request):
    """Render a paginated, searchable card-style list of users that extends admin dashboard."""
    # Basic auth guard: require jwt_user and ADMIN role (follow adminDashBoard pattern)
    # jwt_user = getattr(request, 'jwt_user', None)
    # role = jwt_user.get('role') if jwt_user else None
    # if jwt_user is None:
    #     return HttpResponse("Unauthorized", status=401)
    # if role and str(role).upper() != 'ADMIN':
    #     return HttpResponse("Forbidden", status=403)
    query = request.GET.get('q', '').strip()
    page_no = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 12))

    qs = User.objects.filter(is_active=True).order_by('-created_at')
    if query:
        qs = qs.filter(
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(contact_no__icontains=query)
        )

    paginator = Paginator(qs, page_size)
    try:
        users_page = paginator.page(page_no)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)

    context = {
        'users_page': users_page,
        'query': query,
        'page_size': page_size,
    }
    print("Rendering user list with context:", context)
    return render(request, 'accounts/userlist.html', context)


@login_required_view
def user_create_view(request):
    """Render a simple user creation page that extends admin dashboard.

    This page posts to the existing API `api/users/create/` via client-side form.
    """
    # jwt_user = getattr(request, 'jwt_user', None)
    # role = jwt_user.get('role') if jwt_user else None
    # if jwt_user is None:
    #     return HttpResponse("Unauthorized", status=401)
    # if role and str(role).upper() != 'ADMIN':
    #     return HttpResponse("Forbidden", status=403)

    return render(request, 'accounts/user_create.html', {})


@login_required_view
def logout_view(request):
    """
    Logout view that clears authentication tokens and redirects to login page.
    Removes JWT token from cookies and localStorage (via client-side script).
    """
    from django.http import JsonResponse
    
    response = JsonResponse({
        "IsSuccess": True,
        "Message": "Logged out successfully"
    })
    
    # Clear authentication cookies
    response.delete_cookie('access_token', path='/')
    response.delete_cookie('user_role', path='/')
    response.delete_cookie('user_name', path='/')
    response.delete_cookie('user_email', path='/')
    response.delete_cookie('csrftoken', path='/')
    
    return response
