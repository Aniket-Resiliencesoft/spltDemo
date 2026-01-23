"""
Event API Views

Endpoints for creating, retrieving, updating, and deleting events.
"""

from django.contrib.auth.hashers import make_password
from django.db.models import Q
from rest_framework import status

from common.api.base_api import BaseAuthenticatedAPI
from events.models import Event
from events.serializers import (
    EventGetSerializer,
    EventCreateSerializer,
    EventUpdateSerializer,
    EventListSerializer,
    EventSummarySerializer,
)


class EventListAPI(BaseAuthenticatedAPI):
    """
    GET: Retrieve all events with pagination and filters
    Supports filters: fromDate, toDate, status, category, search
    """
    
    def get(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Get pagination parameters
        page_no = int(request.query_params.get('pageNo', 1))
        page_size = int(request.query_params.get('pageSize', 10))
        
        # Get optional filters
        from_date = request.query_params.get('fromDate', '').strip()
        to_date = request.query_params.get('toDate', '').strip()
        status_filter = request.query_params.get('status', '').strip()
        category_filter = request.query_params.get('category', '').strip()
        search_filter = request.query_params.get('search', '').strip()
        
        # Base query
        query = Event.objects.filter(is_active=True)

        if request.jwt_user['role'] != "ADMIN":
            query = query.filter(created_by=request.jwt_user['user_id'])

        query = query.order_by('-created_at')
        
        # Apply date filters
        if from_date:
            query = query.filter(event_date__gte=from_date)
        if to_date:
            query = query.filter(event_date__lte=to_date)
        
        # Apply status filter
        if status_filter:
            query = query.filter(status=status_filter)
        
        # Apply category filter
        if category_filter:
            query = query.filter(category=category_filter)
        
        # Apply search filter (search in title and description)
        if search_filter:
            query = query.filter(
                Q(title__icontains=search_filter) | 
                Q(description__icontains=search_filter)
            )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Calculate offset
        offset = (page_no - 1) * page_size
        
        # Get events for this page
        events = query[offset:offset + page_size]
        
        # Serialize
        serializer = EventListSerializer(events, many=True)
        
        # Return paginated response with total record count
        return self.paginated_response(
            data=serializer.data,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
            message="Events retrieved successfully"
        )


class EventDetailAPI(BaseAuthenticatedAPI):
    """
    GET: Retrieve single event by ID
    """
    
    def get(self, request, event_id):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Get event
        try:
            event = Event.objects.get(id=event_id, is_active=True)
        except Event.DoesNotExist:
            return self.error_response(
                message="Event not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize
        serializer = EventGetSerializer(event)
        
        # Return response
        return self.success_response(
            data=serializer.data,
            message="Event retrieved successfully"
        )


class EventCreateAPI(BaseAuthenticatedAPI):
    """
    POST: Create a new event
    Requires authentication
    """
    
    def post(self, request):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Validate input
        serializer = EventCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                message="Validation failed",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create event with current user as creator
        event = serializer.save(created_by_id=request.jwt_user['user_id'])
        
        # Return created event
        response_serializer = EventGetSerializer(event)
        return self.success_response(
            data=response_serializer.data,
            message="Event created successfully",
            status_code=status.HTTP_201_CREATED
        )


class EventUpdateAPI(BaseAuthenticatedAPI):
    """
    PUT: Update event (full update)
    PATCH: Partial update event
    
    Only event creator or ADMIN can update
    """
    
    def put(self, request, event_id):
        return self._update_event(request, event_id, partial=False)
    
    def patch(self, request, event_id):
        return self._update_event(request, event_id, partial=True)
    
    def _update_event(self, request, event_id, partial=False):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Get event
        try:
            event = Event.objects.get(id=event_id, is_active=True)
        except Event.DoesNotExist:
            return self.error_response(
                message="Event not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization (creator or admin)
        jwt_user_id = request.jwt_user.get('user_id')
        jwt_role = request.jwt_user.get('role')
        
        if jwt_role != 'ADMIN' and event.created_by_id != jwt_user_id:
            return self.error_response(
                message="Permission denied",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Update event
        serializer = EventUpdateSerializer(
            event,
            data=request.data,
            partial=partial
        )
        
        if not serializer.is_valid():
            return self.error_response(
                message="Validation failed",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        
        # Return updated event
        response_serializer = EventGetSerializer(event)
        return self.success_response(
            data=response_serializer.data,
            message="Event updated successfully"
        )


class EventDeleteAPI(BaseAuthenticatedAPI):
    """
    DELETE: Soft delete event (set is_active=False)
    
    Only event creator or ADMIN can delete
    """
    
    def delete(self, request, event_id):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Get event
        try:
            event = Event.objects.get(id=event_id, is_active=True)
        except Event.DoesNotExist:
            return self.error_response(
                message="Event not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization (creator or admin)
        jwt_user_id = request.jwt_user.get('user_id')
        jwt_role = request.jwt_user.get('role')
        
        if jwt_role != 'ADMIN' and event.created_by_id != jwt_user_id:
            return self.error_response(
                message="Permission denied",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete
        event.is_active = False
        event.save()
        
        # Return success
        return self.success_response(
            message="Event deleted successfully"
        )


class EventStatusUpdateAPI(BaseAuthenticatedAPI):
    """
    PATCH: Update event status only
    
    Transitions:
        draft -> active -> closed -> completed
        Any state -> cancelled
    """
    
    def patch(self, request, event_id):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        # Get event
        try:
            event = Event.objects.get(id=event_id, is_active=True)
        except Event.DoesNotExist:
            return self.error_response(
                message="Event not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization (creator or admin)
        jwt_user_id = request.jwt_user.get('user_id')
        jwt_role = request.jwt_user.get('role')
        
        if jwt_role != 'ADMIN' and event.created_by_id != jwt_user_id:
            return self.error_response(
                message="Permission denied",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Get new status
        new_status = request.data.get('status')
        
        if not new_status:
            return self.error_response(
                message="Status is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status
        valid_statuses = [choice[0] for choice in Event.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return self.error_response(
                message=f"Invalid status. Valid options: {', '.join(valid_statuses)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status
        event.status = new_status
        event.save()
        
        # Return updated event
        serializer = EventGetSerializer(event)
        return self.success_response(
            data=serializer.data,
            message="Event status updated successfully"
        )


class EventSummaryAPI(BaseAuthenticatedAPI):
    """GET: Return an event summary including members, amounts and dates."""

    def get(self, request, event_id):
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error

        try:
            event = Event.objects.get(id=event_id, is_active=True)
        except Event.DoesNotExist:
            return self.error_response(
                message="Event not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Build summary using model helper
        summary = event.get_summary()

        # Validate/serialize output
        serializer = EventSummarySerializer(summary)

        return self.success_response(
            data=serializer.data,
            message="Event summary retrieved successfully"
        )
