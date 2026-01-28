"""
Event API Views

Endpoints for creating, retrieving, updating, and deleting events.
"""

from django.contrib.auth.hashers import make_password
from django.db.models import Q, Sum, Count, F
from rest_framework import status

from common.api.base_api import BaseAuthenticatedAPI
from events.models import Event
from payments.models import EventCollectionTransaction
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
    Data is grouped by eventId and userId (creator)
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
            query = query.filter(created_by_id=request.jwt_user['user_id'])

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
        
        # Serialize and group by eventId and userId
        serialized_data = []
        for event in events:
            # Aggregate participants data
            participants_count = EventCollectionTransaction.objects.filter(
                event_id=event.id,
                is_active=True
            ).values('user_id').distinct().count()
            
            # Aggregate contributions
            total_contributed = EventCollectionTransaction.objects.filter(
                event_id=event.id,
                is_active=True
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            serializer = EventListSerializer(event)
            event_data = serializer.data
            event_data['event_id'] = event.id
            event_data['created_by_id'] = event.created_by_id
            event_data['total_event_amount'] = float(event.event_amount)
            event_data['participants_count'] = participants_count
            event_data['total_contributed'] = float(total_contributed)
            
            serialized_data.append(event_data)
        
        # Return paginated response with total record count
        return self.paginated_response(
            data=serialized_data,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
            message="Events retrieved successfully"
        )


class EventJoinedListAPI(BaseAuthenticatedAPI):
    """
    GET: Retrieve all events that user has joined - Grouped by eventId and userId
    Shows events where user has a transaction record (joined)
    Data is aggregated per event per user
    Supports filters: fromDate, toDate, category, search
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
        category_filter = request.query_params.get('category', '').strip()
        search_filter = request.query_params.get('search', '').strip()
        
        # Get current user ID
        current_user_id = request.jwt_user['user_id']
        
        # Get all transactions grouped by event and user
        transactions_query = EventCollectionTransaction.objects.filter(
            user_id=current_user_id,
            is_active=True
        ).select_related('event', 'user')
        
        # Get distinct event IDs where user has joined
        joined_event_ids = transactions_query.values_list('event_id', flat=True).distinct()
        
        # Base query: events user has joined
        query = Event.objects.filter(
            id__in=joined_event_ids,
            is_active=True
        ).exclude(created_by_id=current_user_id).order_by('-created_at')
        
        # Apply date filters
        if from_date:
            query = query.filter(event_date__gte=from_date)
        if to_date:
            query = query.filter(event_date__lte=to_date)
        
        # Apply category filter
        if category_filter:
            query = query.filter(category=category_filter)
        
        # Apply search filter
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
        
        # Group data by eventId and userId
        serialized_data = []
        for event in events:
            # Aggregate transactions for this event by current user
            user_transactions = EventCollectionTransaction.objects.filter(
                event_id=event.id,
                user_id=current_user_id,
                is_active=True
            ).aggregate(
                total_contributed=Sum('amount'),
                transaction_count=Count('id')
            )
            
            # Get the latest transaction to get status
            latest_transaction = EventCollectionTransaction.objects.filter(
                event_id=event.id,
                user_id=current_user_id,
                is_active=True
            ).latest('created_at', default=None)
            
            serializer = EventListSerializer(event)
            event_data = serializer.data
            event_data['status'] = 'joined'
            event_data['total_event_amount'] = float(event.event_amount)
            event_data['contributed_amount'] = float(user_transactions['total_contributed'] or 0.0)
            event_data['transaction_count'] = user_transactions['transaction_count'] or 0
            event_data['transaction_status'] = latest_transaction.status if latest_transaction else 'pending'
            event_data['user_id'] = current_user_id
            event_data['event_id'] = event.id
            
            serialized_data.append(event_data)
        
        # Return paginated response with total record count
        return self.paginated_response(
            data=serialized_data,
            page_no=page_no,
            page_size=page_size,
            total_record=total_count,
            message="Joined events retrieved successfully (grouped by eventId and userId)"
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


class EventShareLinkAPI(BaseAuthenticatedAPI):
    """
    GET: Generate a shareable URL for an event
    The URL includes event ID and pre-calculated per-person amount
    
    Response:
    {
        "IsSuccess": true,
        "Data": {
            "event_id": 123,
            "event_title": "Birthday Party",
            "share_link": "http://domain.com/join/event/?event_id=123&amount=500.00",
            "per_person_amount": 500.00,
            "total_amount": 2500.00,
            "persons_count": 5
        }
    }
    """
    
    def get(self, request, event_id):
        # Check authentication
        auth_error = self.require_authentication(request)
        if auth_error:
            return auth_error
        
        try:
            # Get the event
            event = Event.objects.get(id=event_id, is_active=True)
        except Event.DoesNotExist:
            return self.error_response(
                message="Event not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Import utility function
        from events.utils import generate_event_share_url
        
        # Generate share URL
        share_data = generate_event_share_url(event, request=request)
        
        # Return success response
        return self.success_response(
            data={
                'event_id': share_data['event_id'],
                'event_title': share_data['event_title'],
                'share_link': share_data['share_link'],
                'relative_link': share_data['relative_url'],
                'per_person_amount': float(share_data['per_person_amount']),
                'total_amount': float(share_data['total_amount']),
                'persons_count': share_data['persons_count'],
                'event_category': share_data['event_category'],
            },
            message="Event share link generated successfully"
        )

