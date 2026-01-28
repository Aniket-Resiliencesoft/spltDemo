from django.shortcuts import render
from common.decorators import login_required_view


@login_required_view
def list_payment_page(request):
    """Render a simple payments list page placeholder."""
    return render(request, 'payments/list_payment.html', {})
