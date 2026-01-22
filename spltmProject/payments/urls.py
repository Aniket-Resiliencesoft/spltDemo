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

urlpatterns = [
    # List and Create
    path('transactions/', TransactionListAPI.as_view()),
    path('transactions/create/', TransactionCreateAPI.as_view()),
    
    # Detail, Update, Delete
    path('transactions/<int:transaction_id>/', TransactionDetailAPI.as_view()),
    path('transactions/<int:transaction_id>/update/', TransactionUpdateAPI.as_view()),
    path('transactions/<int:transaction_id>/delete/', TransactionDeleteAPI.as_view()),
    
    # Summary and History
    path('events/<int:event_id>/summary/', EventTransactionSummaryAPI.as_view()),
    path('events/<int:event_id>/users/<int:user_id>/history/', UserTransactionHistoryAPI.as_view()),
]
