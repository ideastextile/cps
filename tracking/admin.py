from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Driver, Parcel, TrackingEvent, Job, Notification, AboutSection, DriverLocationHistory, Route

@admin.register(AboutSection)
class AboutAdmin(admin.ModelAdmin):
    list_display = ('heading', 'experience_years')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'first_name', 'last_name', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'address')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'address')}),
    )


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle_details', 'is_available', 'is_active', 'current_latitude', 'current_longitude', 'last_location_update')
    list_filter = ('is_available', 'is_active', 'last_location_update')
    search_fields = ('user__username', 'user__email', 'vehicle_details')
    readonly_fields = ('last_location_update', 'last_route_update')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'vehicle_details')
        }),
        ('Status', {
            'fields': ('is_available', 'is_active')
        }),
        ('Location Tracking', {
            'fields': ('current_latitude', 'current_longitude', 'last_location_update', 'location_accuracy')
        }),
        ('Performance', {
            'fields': ('total_distance_today', 'last_route_update')
        }),
    )


@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'customer', 'status', 'current_driver', 'booked_at', 'expected_delivery_date','can_customer_track')
    list_filter = ('status', 'booked_at','can_customer_track')
    search_fields = ('tracking_number', 'customer__username', 'recipient_name', 'pickup_address', 'delivery_address')
    readonly_fields = ('tracking_number', 'booked_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('tracking_number', 'customer', 'status', 'current_driver')
        }),
        ('Addresses', {
            'fields': ('pickup_address', 'delivery_address', 'recipient_name', 'recipient_phone')
        }),
        ('Parcel Details', {
            'fields': ('description', 'weight', 'dimensions', 'delivery_instructions', 'can_customer_track')
        }),
        ('Timestamps', {
            'fields': ('booked_at', 'expected_delivery_date')
        }),
    )


@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    list_display = ('parcel', 'status_update', 'timestamp', 'location', 'created_by')
    list_filter = ('timestamp', 'status_update')
    search_fields = ('parcel__tracking_number', 'status_update', 'location', 'notes')
    readonly_fields = ('timestamp',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('parcel', 'driver', 'job_type', 'status', 'assigned_at', 'accepted_at', 'completed_at', 'customer_tracking_enabled')
    list_filter = ('job_type', 'status', 'assigned_at', 'customer_tracking_enabled', 'location_access_enabled')
    search_fields = ('parcel__tracking_number', 'driver__user__username')
    readonly_fields = ('assigned_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('parcel', 'driver', 'job_type', 'status')
        }),
        ('Timing', {
            'fields': ('assigned_at', 'accepted_at', 'completed_at', 'estimated_arrival_time')
        }),
        ('Route Management', {
            'fields': ('route_started_at', 'route_completed_at', 'estimated_distance', 'actual_distance', 'route_waypoints')
        }),
        ('Tracking Permissions', {
            'fields': ('location_access_enabled', 'customer_tracking_enabled', 'tracking_start_time', 'tracking_end_time')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at', 'parcel')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)




@admin.register(DriverLocationHistory)
class DriverLocationHistoryAdmin(admin.ModelAdmin):
    list_display = ('driver', 'latitude', 'longitude', 'timestamp', 'accuracy', 'speed', 'current_job')
    list_filter = ('timestamp', 'driver', 'current_job')
    search_fields = ('driver__user__username', 'current_job__parcel__tracking_number')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Location Data', {
            'fields': ('driver', 'latitude', 'longitude', 'timestamp', 'accuracy')
        }),
        ('Movement Data', {
            'fields': ('speed', 'heading')
        }),
        ('Job Association', {
            'fields': ('current_job',)
        }),
    )


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('route_name', 'route_area', 'depot', 'driver', 'status', 'started_at', 'completed_at')
    list_filter = ('status', 'route_area', 'depot', 'started_at', 'completed_at')
    search_fields = ('route_name', 'route_area', 'depot', 'driver__user__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('route_name', 'route_area', 'depot', 'driver', 'status')
        }),
        ('Planning', {
            'fields': ('planned_stops', 'estimated_duration', 'estimated_distance')
        }),
        ('Execution', {
            'fields': ('started_at', 'completed_at', 'actual_duration', 'actual_distance')
        }),
        ('Optimization', {
            'fields': ('optimized_order', 'optimization_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

