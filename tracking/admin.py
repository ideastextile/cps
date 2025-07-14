from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Driver, Parcel, TrackingEvent, Job, Notification ,AboutSection

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
    list_display = ('user', 'vehicle_details', 'is_available', 'current_latitude', 'current_longitude')
    list_filter = ('is_available',)
    search_fields = ('user__username', 'user__email', 'vehicle_details')


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
    list_display = ('parcel', 'driver', 'job_type', 'status', 'assigned_at', 'accepted_at', 'completed_at')
    list_filter = ('job_type', 'status', 'assigned_at')
    search_fields = ('parcel__tracking_number', 'driver__user__username')
    readonly_fields = ('assigned_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at', 'parcel')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)

