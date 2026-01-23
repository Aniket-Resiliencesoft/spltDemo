from django.urls import path
from events.api_views.event_api import (
    EventListAPI,
    EventDetailAPI,
    EventCreateAPI,
    EventSummaryAPI,
    EventUpdateAPI,
    EventDeleteAPI,
    EventStatusUpdateAPI,
)
from . import ui_views

urlpatterns = [
    # List and Create
    path('api/events/', EventListAPI.as_view()),
    path('api/events/create/', EventCreateAPI.as_view()),
    
    # Detail, Update, Delete
    path('api/events/<int:event_id>/', EventDetailAPI.as_view()),
    path('api/events/<int:event_id>/update/', EventUpdateAPI.as_view()),
    path('api/events/<int:event_id>/delete/', EventDeleteAPI.as_view()),
    
    # Status update
    path('api/events/<int:event_id>/status/', EventStatusUpdateAPI.as_view()),
    # Summary
    path('api/events/<int:event_id>/summary/', EventSummaryAPI.as_view()),
    # UI create event page
    path('create/event/', ui_views.create_event_page),
    # UI events list page (standalone)
    path('list/events/', ui_views.list_events_page, name='list_events'),
]
