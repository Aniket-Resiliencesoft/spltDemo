"""
Serializers for Event model
"""

from rest_framework import serializers
from events.models import Event
from decimal import Decimal, ROUND_HALF_UP

class EventGetSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    per_person_amount = serializers.SerializerMethodField()

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
            'due_pay_date_time',
            'latitude',
            'longitude',
            'persons_count',
            'event_amount',
            'per_person_amount',  # ✅
            'status',
            'status_display',
            'created_by',
            'created_by_name',
            'is_active',
            'created_at',
            'updated_at',
            'location',
            'custom_category',
            'vendor_name',
        ]

    def get_per_person_amount(self, obj):
        if not obj.persons_count or not obj.event_amount:
            return "0.00"

        return round(obj.event_amount / obj.persons_count, 2)


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
            'due_pay_date_time',
            'latitude',
            'longitude',
            'persons_count',
            'event_amount',
            'status',
            'location',
            'custom_category',
            'vendor_name',
        ]
    
    def validate(self, data):
        """
        Validates event dates.

        Rules:
        - start_date_time < end_date_time
        - due_pay_date_time must be <= start_date_time
        - due_pay_date_time.date() must be <= event_date
        - persons_count >= 1
        """

        start_dt = data.get('start_date_time')      # datetime
        end_dt = data.get('end_date_time')          # datetime
        due_dt = data.get('due_pay_date_time')      # datetime
        event_date = data.get('event_date')         # date

        # 1️⃣ Start must be before end
        if start_dt and end_dt and start_dt >= end_dt:
            raise serializers.ValidationError(
                "Start datetime must be before end datetime."
            )

        # 2️⃣ Due date must be before or equal to start datetime
        if due_dt and start_dt and due_dt > start_dt:
            raise serializers.ValidationError(
                "Due pay date must be before event start time."
            )

        # 3️⃣ Due date must not be after event date
        if due_dt and event_date and due_dt.date() > event_date:
            raise serializers.ValidationError(
                "Due pay date cannot be after event date."
            )

        # 4️⃣ Persons count validation
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
            'due_pay_date_time',
            'latitude',
            'longitude',
            'persons_count',
            'status',
            'location',
            'custom_category',
            'vendor_name',
        ]
    
    def validate(self, data):
        """Validates event dates on update"""
        start_dt = data.get('start_date_time', self.instance.start_date_time)
        end_dt = data.get('end_date_time', self.instance.end_date_time)
        due_date = data.get('due_pay_date_time', self.instance.due_pay_date_time)
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
    due_date = serializers.DateTimeField()
    collected_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    created_by = serializers.DictField(allow_null=True)
    event_date = serializers.DateField()
    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField()
    # Vendor payouts summary and list (added to include payout details)
    vendor_payouts_summary = serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=2), allow_empty=True)
    vendor_payouts = serializers.ListField(child=serializers.DictField(), allow_empty=True)
