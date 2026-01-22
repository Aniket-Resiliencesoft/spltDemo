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
    path('api/transactions/', TransactionListAPI.as_view()),
    path('api/transactions/create/', TransactionCreateAPI.as_view()),
    
    # Detail, Update, Delete
    path('api/transactions/<int:transaction_id>/', TransactionDetailAPI.as_view()),
    path('api/transactions/<int:transaction_id>/update/', TransactionUpdateAPI.as_view()),
    path('api/transactions/<int:transaction_id>/delete/', TransactionDeleteAPI.as_view()),
    
    # Summary and History
    path('api/events/<int:event_id>/summary/', EventTransactionSummaryAPI.as_view()),
    path('api/events/<int:event_id>/users/<int:user_id>/history/', UserTransactionHistoryAPI.as_view()),
]
