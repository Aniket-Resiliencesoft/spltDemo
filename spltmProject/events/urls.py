from django.urls import path
from events.api_views.event_api import (
    EventListAPI,
    EventDetailAPI,
    EventCreateAPI,
    EventUpdateAPI,
    EventDeleteAPI,
    EventStatusUpdateAPI,
)
from events import ui_views

urlpatterns = [
    # List and Create
    path('events/', EventListAPI.as_view()),
    path('events/create/', EventCreateAPI.as_view()),
    
    # Detail, Update, Delete
    path('events/<int:event_id>/', EventDetailAPI.as_view()),
    path('events/<int:event_id>/update/', EventUpdateAPI.as_view()),
    path('events/<int:event_id>/delete/', EventDeleteAPI.as_view()),
    
    # Status update
    path('events/<int:event_id>/status/', EventStatusUpdateAPI.as_view()),
]

# for Ui
urlpatterns +=[
    path('getevents/',ui_views.events, name='events')
]
