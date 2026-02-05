from django.urls import path
from payments.api_views.transaction_api import (
    TransactionListAPI,
    TransactionDetailAPI,
    TransactionCreateAPI,
    TransactionUpdateAPI,
    TransactionDeleteAPI,
    EventTransactionSummaryAPI,
    UserTransactionHistoryAPI,
    UserPaymentsSummaryAPI,
    VendorPaymentCreateAPI,
    VendorPaymentListAPI,
    VendorPaymentPayoutAPI,
    VendorPaymentRefreshStatusAPI,
    VendorPaymentStatusAPI,
    VendorPaymentCreateWalletAPI,
    VendorPaymentPayoutWalletAPI,
    OrganizerWalletBalanceAPI,
)
from payments.api_views.razorpay_webhook import razorpay_webhook
from payments.api_views.razorpay_config_api import RazorpayConfigAPI
from .api_views import (
    CreateOrderAPI,
    VerifyPaymentAPI,
    GetWalletBalanceAPI,
    GetWalletLedgerAPI,
    InitiatePayoutAPI,
    WebhookHandlerAPI,
    SettleToVendorAPI,
    GetSettlementSummaryAPI
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
    path('api/users/<int:user_id>/payments/summary/', UserPaymentsSummaryAPI.as_view()),
    
    # Razorpay Payment APIs
    path('api/payments/create-order/', CreateOrderAPI.as_view(), name='create-order'),
    path('api/payments/verify-payment/', VerifyPaymentAPI.as_view(), name='verify-payment'),
    path('api/payments/wallet/balance/', GetWalletBalanceAPI.as_view(), name='wallet-balance'),
    path('api/payments/wallet/ledger/', GetWalletLedgerAPI.as_view(), name='wallet-ledger'),
    path('api/payments/payout/initiate/', InitiatePayoutAPI.as_view(), name='initiate-payout'),
    # Razorpay configuration (authenticated)
    path('api/payments/razorpay-config/', RazorpayConfigAPI.as_view(), name='razorpay-config'),
    path('api/webhooks/razorpay/', WebhookHandlerAPI.as_view(), name='razorpay-webhook'),
    #
     # Step 3: Create vendor payment (DB entry only)
    path('api/payments/vendor/create/',VendorPaymentCreateAPI.as_view(),name='vendor-payment-create'),
    path('api/payments/vendor/', VendorPaymentListAPI.as_view(), name='vendor-payment-list'),

    # Step 4: Trigger Razorpay payout (Owner ➜ Vendor)
    path('api/payments/vendor/<int:transaction_id>/payout/', VendorPaymentPayoutAPI.as_view(), name='vendor-payment-payout' ),

    path("api/payments/vendor/<int:transaction_id>/status/", VendorPaymentStatusAPI.as_view(), name="vendor-payment-status",),

    # refresh payout status from Razorpay (optional)
    path("api/payments/vendor/<int:transaction_id>/refresh-status/", VendorPaymentRefreshStatusAPI.as_view(), name="vendor-payment-refresh-status",),
    
    # =========================
    # WALLET-BASED VENDOR PAYMENT APIs
    # Validates against organizer's total wallet balance
    # across all their events (not event-specific)
    # =========================
    path('api/payments/vendor-wallet/create/', VendorPaymentCreateWalletAPI.as_view(), name='vendor-payment-wallet-create'),
    path('api/payments/vendor-wallet/<int:transaction_id>/payout/', VendorPaymentPayoutWalletAPI.as_view(), name='vendor-payment-wallet-payout'),
    path('api/organizer/wallet/balance/', OrganizerWalletBalanceAPI.as_view(), name='organizer-wallet-balance'),
    # =========================
    # Webhooks
    # =========================
    # Existing generic webhook (if you already use it)
    path('api/payments/webhooks/razorpay/', WebhookHandlerAPI.as_view(), name='razorpay-webhook'),

    # Vendor payout webhook (if you keep it separate)
    path('api/webhooks/razorpay/vendor-payout/', razorpay_webhook, name='razorpay-vendor-payout-webhook'),
    #
    # Event Settlement APIs (Owner distributes to vendors)
    path('api/payments/settle-to-vendor/', SettleToVendorAPI.as_view(), name='settle-to-vendor'),
    path('api/payments/settlement/summary/', GetSettlementSummaryAPI.as_view(), name='settlement-summary'),
    
    # UI payments list page
    path('list/payment/', ui_views.list_payment_page, name='list_payments'),
    path('list/payout/', ui_views.list_payout_page, name='list_payouts'),
]
