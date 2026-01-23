from django.shortcuts import render


def list_payment_page(request):
    """Render a simple payments list page placeholder."""
    return render(request, 'payments/list_payment.html', {})
