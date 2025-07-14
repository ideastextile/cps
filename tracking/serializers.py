from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Driver, Parcel, TrackingEvent, Job, Notification



class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'user_type', 'phone_number', 'address', 'first_name', 'last_name')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create driver profile if user is a driver
        if validated_data.get('user_type') == 'driver':
            Driver.objects.create(user=user)
        
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('User account is disabled.')
            else:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
        else:
            raise serializers.ValidationError('Must include username and password.')

        return data


class DriverSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Driver
        fields = ('user', 'vehicle_details', 'current_latitude', 'current_longitude', 'is_available')


class TrackingEventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = TrackingEvent
        fields = ('id', 'timestamp', 'location', 'status_update', 'notes', 'image', 'signature', 'created_by_name')


class ParcelSerializer(serializers.ModelSerializer):
    tracking_events = TrackingEventSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    driver_name = serializers.CharField(source='current_driver.user.username', read_only=True)
    can_customer_track = serializers.BooleanField(read_only=True)  # ✅ This field added

    class Meta:
        model = Parcel
        fields = ('id', 'tracking_number', 'customer', 'customer_name', 'pickup_address',
                 'delivery_address', 'recipient_name', 'recipient_phone', 'description',
                 'weight', 'dimensions', 'status', 'current_driver', 'driver_name',
                 'booked_at', 'expected_delivery_date', 'delivery_instructions', 'tracking_events', 'can_customer_track')
        read_only_fields = ('tracking_number', 'booked_at')


class ParcelBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parcel
        fields = ('pickup_address', 'delivery_address', 'recipient_name', 'recipient_phone', 
                 'description', 'weight', 'dimensions', 'delivery_instructions')

    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)


class JobSerializer(serializers.ModelSerializer):
    parcel = ParcelSerializer(read_only=True)
    driver_name = serializers.CharField(source='driver.user.username', read_only=True)

    class Meta:
        model = Job
        fields = ('id', 'parcel', 'driver', 'driver_name', 'job_type', 'status', 
                 'assigned_at', 'accepted_at', 'completed_at', 'notes')


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'is_read', 'created_at', 'parcel')


# class ParcelTrackingSerializer(serializers.ModelSerializer):
#     tracking_events = TrackingEventSerializer(many=True, read_only=True)

#     class Meta:
#         model = Parcel
#         fields = ('tracking_number', 'status', 'pickup_address', 'delivery_address', 
#                  'recipient_name', 'booked_at', 'expected_delivery_date', 'tracking_events')

class ParcelTrackingSerializer(serializers.ModelSerializer):
    tracking_events = TrackingEventSerializer(many=True, read_only=True)
    driver_latitude = serializers.FloatField(source='current_driver.current_latitude', read_only=True)
    driver_longitude = serializers.FloatField(source='current_driver.current_longitude', read_only=True)


    class Meta:
        model = Parcel
        fields = (
            'tracking_number', 'status', 'pickup_address', 'delivery_address', 
            'recipient_name', 'booked_at', 'expected_delivery_date', 
            'tracking_events', 'driver_latitude', 'driver_longitude'
        )
class DriverLocationUpdateSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

    def get_driver_latitude(self, obj):
        if obj.status == 'out_for_delivery' and obj.current_driver:
            return obj.current_driver.current_latitude
        return None

    def get_driver_longitude(self, obj):
        if obj.status == 'out_for_delivery' and obj.current_driver:
            return obj.current_driver.current_longitude
        return None

class DeliveryCompletionSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)
    delivery_image = serializers.ImageField(required=False)
    signature = serializers.ImageField(required=False)

