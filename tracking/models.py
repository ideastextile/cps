from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid
from django.contrib.auth import get_user_model
# User = get_user_model()  # ❌ This should NOT be at the top of models.py


class User(AbstractUser):
    USER_TYPES = (
        ('customer', 'Customer'),
        ('controller', 'Controller'),
        ('driver', 'Driver'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.username} ({self.user_type})"


class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    vehicle_details = models.TextField(blank=True)
    
    # Enhanced location tracking fields
    current_latitude = models.FloatField(null=True, blank=True)
    current_longitude = models.FloatField(null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    location_accuracy = models.FloatField(null=True, blank=True, help_text="GPS accuracy in meters")
    
    # Status and availability
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False, help_text="Currently on duty")
    
    # Route and performance tracking
    total_distance_today = models.FloatField(default=0.0, help_text="Distance in kilometers")
    last_route_update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Driver: {self.user.username}"


class Parcel(models.Model):
    STATUS_CHOICES = (
        ('order_placed', 'Order Placed'),
        ('awaiting_pickup', 'Awaiting Pickup'),
        ('collected', 'Collected'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed_delivery', 'Failed Delivery'),
        ('cancelled', 'Cancelled'),
    )

    tracking_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parcels')
    pickup_address = models.TextField()
    delivery_address = models.TextField()
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=20)
    description = models.TextField()
    weight = models.FloatField(help_text="Weight in kg")
    dimensions = models.CharField(max_length=100, help_text="L x W x H in cm")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='order_placed')
    current_driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    booked_at = models.DateTimeField(default=timezone.now)
    expected_delivery_date = models.DateTimeField(null=True, blank=True)
    delivery_instructions = models.TextField(blank=True)

    # ✅ New fields
    can_customer_track = models.BooleanField(default=False)
    sequence_number = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Parcel {self.tracking_number} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)


class TrackingEvent(models.Model):
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name='tracking_events')
    timestamp = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=200, blank=True)
    status_update = models.CharField(max_length=100)
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to='tracking_images/', null=True, blank=True)
    signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.parcel.tracking_number} - {self.status_update} at {self.timestamp}"


class Job(models.Model):
    JOB_TYPES = (
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
        
    )

    JOB_STATUS = (
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('en_route', 'En Route'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name='jobs')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='jobs')
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    status = models.CharField(max_length=20, choices=JOB_STATUS, default='assigned')
    assigned_at = models.DateTimeField(default=timezone.now)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # Enhanced route tracking fields
    estimated_arrival_time = models.DateTimeField(null=True, blank=True)
    location_access_enabled = models.BooleanField(default=False)
    
    # New route management fields
    route_started_at = models.DateTimeField(null=True, blank=True)
    route_completed_at = models.DateTimeField(null=True, blank=True)
    estimated_distance = models.FloatField(null=True, blank=True, help_text="Distance in kilometers")
    actual_distance = models.FloatField(null=True, blank=True, help_text="Distance in kilometers")
    route_waypoints = models.JSONField(default=list, blank=True, help_text="Store route coordinates")
    
    # Customer tracking permissions
    customer_tracking_enabled = models.BooleanField(default=False)
    tracking_start_time = models.DateTimeField(null=True, blank=True)
    tracking_end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.job_type} job for {self.parcel.tracking_number} - {self.status}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"


class DriverLocationHistory(models.Model):
    """Model to store historical location data for route tracking and analytics"""
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='location_history')
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)
    accuracy = models.FloatField(null=True, blank=True, help_text="GPS accuracy in meters")
    speed = models.FloatField(null=True, blank=True, help_text="Speed in km/h")
    heading = models.FloatField(null=True, blank=True, help_text="Direction in degrees")
    
    # Associated job information
    current_job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['driver', '-timestamp']),
            models.Index(fields=['current_job', '-timestamp']),
        ]

    def __str__(self):
        return f"Location for {self.driver.user.username} at {self.timestamp}"


class Route(models.Model):
    """Model for managing and storing route information"""
    ROUTE_STATUS = (
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='routes')
    route_name = models.CharField(max_length=100)
    route_area = models.CharField(max_length=50, help_text="e.g., PE21, Route 21")
    depot = models.CharField(max_length=50, help_text="e.g., Depot 3")
    
    # Route planning
    planned_stops = models.JSONField(default=list, help_text="List of stop coordinates")
    estimated_duration = models.DurationField(null=True, blank=True)
    estimated_distance = models.FloatField(null=True, blank=True, help_text="Distance in kilometers")
    
    # Route execution
    status = models.CharField(max_length=20, choices=ROUTE_STATUS, default='planned')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    actual_duration = models.DurationField(null=True, blank=True)
    actual_distance = models.FloatField(null=True, blank=True, help_text="Distance in kilometers")
    
    # Route optimization
    optimized_order = models.JSONField(default=list, blank=True)
    optimization_score = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['driver', 'status']),
            models.Index(fields=['route_area']),
        ]

    def __str__(self):
        return f"Route {self.route_name} - {self.route_area} ({self.status})"


class AboutSection(models.Model):
    heading = models.CharField(max_length=200)
    sub_heading = models.CharField(max_length=100)
    description = models.TextField()
    experience_years = models.CharField(max_length=50, default="25+ Years Experience")
    image = models.ImageField(upload_to='about/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.heading