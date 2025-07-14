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
    current_latitude = models.FloatField(null=True, blank=True)
    current_longitude = models.FloatField(null=True, blank=True)
    is_available = models.BooleanField(default=True)

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

    # ✅ New fields
    estimated_arrival_time = models.DateTimeField(null=True, blank=True)
    location_access_enabled = models.BooleanField(default=False)

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





class AboutSection(models.Model):
    heading = models.CharField(max_length=200)
    sub_heading = models.CharField(max_length=100)
    description = models.TextField()
    experience_years = models.CharField(max_length=50, default="25+ Years Experience")
    image = models.ImageField(upload_to='about/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.heading