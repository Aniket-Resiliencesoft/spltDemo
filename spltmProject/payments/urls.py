from django.urls import path
from payments.api_views.transaction_api import (
    TransactionListAPI,
    TransactionDetailAPI,
    TransactionCreateAPI,
    TransactionUpdateAPI,
    TransactionDeleteAPI,
    EventTransactionSummaryAPI,
    UserTransactionHistoryAPI,
)
from .api_views import (
    CreateOrderAPI,
    GetWalletBalanceAPI,
    GetWalletLedgerAPI,
    InitiatePayoutAPI,
    WebhookHandlerAPI
)
from . import ui_views

urlpatterns = [
    # List and Create
    path('api/transactions/', TransactionListAPI.as_view()),
    path('api/transactions/create/', TransactionCreateAPI.as_view()),
    
    # Detail, Update, Delete
    path('api/transactions/<int:transaction_id>/', TransactionDetailAPI.as_view()),
    path('api/transactions/<int:transaction_id>/update/', TransactionUpdateAPI.as_view()),
    path('api/transactions/<int:transaction_id>/delete/', TransactionDeleteAPI.as_view()),
    
    # Summary and History
    path('api/events/<int:event_id>/summary/', EventTransactionSummaryAPI.as_view()),
    path('api/events/<int:event_id>/users/<int:user_id>/history/', UserTransactionHistoryAPI.as_view()),
    
    # Razorpay Payment APIs
    path('api/payments/create-order/', CreateOrderAPI.as_view(), name='create-order'),
    path('api/payments/wallet/balance/', GetWalletBalanceAPI.as_view(), name='wallet-balance'),
    path('api/payments/wallet/ledger/', GetWalletLedgerAPI.as_view(), name='wallet-ledger'),
    path('api/payments/payout/initiate/', InitiatePayoutAPI.as_view(), name='initiate-payout'),
    path('api/webhooks/razorpay/', WebhookHandlerAPI.as_view(), name='razorpay-webhook'),
    
    # UI payments list page
    path('list/payment/', ui_views.list_payment_page, name='list_payments'),
]
