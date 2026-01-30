"""
Serializers for EventCollectionTransaction model
"""

from rest_framework import serializers
from payments.models import EventCollectionTransaction, VendorPaymentTransaction


class EventCollectionTransactionGetSerializer(serializers.ModelSerializer):
    """Read-only serializer for retrieving transaction details"""
    
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EventCollectionTransaction
        fields = [
            'id',
            'event',
            'event_title',
            'user',
            'user_name',
            'amount',
            'transaction_type',
            'transaction_type_display',
            'status',
            'status_display',
            'description',
            'payment_method',
            'transaction_date',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'transaction_date',
            'created_at',
            'updated_at',
        ]


class EventCollectionTransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions"""
    
    class Meta:
        model = EventCollectionTransaction
        fields = [
            'event',
            'user',
            'amount',
            'transaction_type',
            'status',
            'description',
            'payment_method',
        ]
    
    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value


class EventCollectionTransactionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating transactions"""
    
    class Meta:
        model = EventCollectionTransaction
        fields = [
            'transaction_type',
            'status',
            'description',
            'payment_method',
        ]


class EventCollectionTransactionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EventCollectionTransaction
        fields = [
            'id',
            'event',
            'event_title',
            'user',
            'user_name',
            'amount',
            'transaction_type',
            'transaction_type_display',
            'status',
            'status_display',
            'transaction_date',
        ]

class VendorPaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorPaymentTransaction
        fields = (
            'event',
            'initiated_by',
            'vendor_name',
            'vendor_upi',
            'amount',
            'purpose',
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_vendor_upi(self, value):
        if '@' not in value:
            raise serializers.ValidationError("Invalid UPI ID.")
        return value

class VendorPaymentGetSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = VendorPaymentTransaction
        fields = [
            'id',
            'event',
            'initiated_by',
            'vendor_name',
            'vendor_upi',
            'amount',
            'purpose',
            'status',
            'status_display',
            'failure_reason',
            'razorpay_payout_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

