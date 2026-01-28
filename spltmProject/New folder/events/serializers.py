"""
Serializers for Event model
"""

from rest_framework import serializers
from events.models import Event


class EventGetSerializer(serializers.ModelSerializer):
    """Read-only serializer for retrieving event details"""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'category',
            'category_display',
            'description',
            'event_date',
            'start_date_time',
            'end_date_time',
            'due_pay_date',
            'latitude',
            'longitude',
            'persons_count',
            'status',
            'status_display',
            'created_by',
            'created_by_name',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]


class EventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new events"""
    
    class Meta:
        model = Event
        fields = [
            'title',
            'category',
            'description',
            'event_date',
            'start_date_time',
            'end_date_time',
            'due_pay_date',
            'latitude',
            'longitude',
            'persons_count',
            'event_amount',
            'status',
        ]
    
    def validate(self, data):
        """
        Validates event dates.
        Ensures: event_date <= start_date_time < end_date_time <= due_pay_date
        """
        start_dt = data.get('start_date_time')
        end_dt = data.get('end_date_time')
        due_date = data.get('due_pay_date')
        event_date = data.get('event_date')
        event_amount = data.get('event_amount')
        if start_dt >= end_dt:
            raise serializers.ValidationError(
                "Start datetime must be before end datetime."
            )
        
        if due_date and due_date > event_date:
            raise serializers.ValidationError(
                "Due pay date cannot be after event date."
            )
        
        if data.get('persons_count', 1) < 1:
            raise serializers.ValidationError(
                "Persons count must be at least 1."
            )
        
        return data


class EventUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating events"""
    
    class Meta:
        model = Event
        fields = [
            'title',
            'category',
            'description',
            'event_date',
            'start_date_time',
            'end_date_time',
            'due_pay_date',
            'latitude',
            'longitude',
            'persons_count',
            'status',
        ]
    
    def validate(self, data):
        """Validates event dates on update"""
        start_dt = data.get('start_date_time', self.instance.start_date_time)
        end_dt = data.get('end_date_time', self.instance.end_date_time)
        due_date = data.get('due_pay_date', self.instance.due_pay_date)
        event_date = data.get('event_date', self.instance.event_date)
        
        if start_dt >= end_dt:
            raise serializers.ValidationError(
                "Start datetime must be before end datetime."
            )
        
        if due_date and due_date < event_date:
            raise serializers.ValidationError(
                "Due pay date cannot be before event date."
            )
        
        return data


class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'category',
            'category_display',
            'event_date',
            'status',
            'status_display',
            'persons_count',
            'created_by_name',
        ]


class EventSummarySerializer(serializers.Serializer):
    """Serializer for event summary returned by `Event.get_summary()`."""

    members = serializers.ListField(child=serializers.DictField(), allow_empty=True)
    due_date = serializers.DateField()
    collected_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    created_by = serializers.DictField(allow_null=True)
    event_date = serializers.DateField()
    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField()
