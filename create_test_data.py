#!/usr/bin/env python3
"""
Script to create test data for the parcel tracking system
"""
import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parcel_tracking_system.settings')
django.setup()

from tracking.models import User, Driver, Parcel, TrackingEvent, Job, Notification

def create_test_data():
    print("Creating test data...")
    
    # Create test users
    customer1, created = User.objects.get_or_create(
        username='customer1',
        defaults={
            'email': 'customer1@example.com',
            'user_type': 'customer',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+1234567890',
            'address': '123 Main St, City, State 12345'
        }
    )
    if created:
        customer1.set_password('password123')
        customer1.save()
    
    customer2, created = User.objects.get_or_create(
        username='customer2',
        defaults={
            'email': 'customer2@example.com',
            'user_type': 'customer',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone_number': '+1234567891',
            'address': '456 Oak Ave, City, State 12346'
        }
    )
    if created:
        customer2.set_password('password123')
        customer2.save()
    
    controller1, created = User.objects.get_or_create(
        username='controller1',
        defaults={
            'email': 'controller1@example.com',
            'user_type': 'controller',
            'first_name': 'Mike',
            'last_name': 'Johnson',
            'phone_number': '+1234567892'
        }
    )
    if created:
        controller1.set_password('password123')
        controller1.save()
    
    driver_user1, created = User.objects.get_or_create(
        username='driver1',
        defaults={
            'email': 'driver1@example.com',
            'user_type': 'driver',
            'first_name': 'Bob',
            'last_name': 'Wilson',
            'phone_number': '+1234567893'
        }
    )
    if created:
        driver_user1.set_password('password123')
        driver_user1.save()
    
    driver_user2, created = User.objects.get_or_create(
        username='driver2',
        defaults={
            'email': 'driver2@example.com',
            'user_type': 'driver',
            'first_name': 'Alice',
            'last_name': 'Brown',
            'phone_number': '+1234567894'
        }
    )
    if created:
        driver_user2.set_password('password123')
        driver_user2.save()
    
    # Create driver profiles
    driver1, created = Driver.objects.get_or_create(user=driver_user1)
    driver1.vehicle_details = 'Honda Civic, License: ABC-123'
    driver1.current_latitude = 40.7128
    driver1.current_longitude = -74.0060
    driver1.save()
    
    driver2, created = Driver.objects.get_or_create(user=driver_user2)
    driver2.vehicle_details = 'Toyota Camry, License: XYZ-789'
    driver2.current_latitude = 40.7589
    driver2.current_longitude = -73.9851
    driver2.save()
    
    # Create test parcels
    parcel1 = Parcel.objects.create(
        customer=customer1,
        pickup_address='123 Main St, City, State 12345',
        delivery_address='789 Pine St, Another City, State 54321',
        recipient_name='Sarah Johnson',
        recipient_phone='+1234567895',
        description='Electronics - Laptop',
        weight=2.5,
        dimensions='40 x 30 x 5',
        status='collected',
        current_driver=driver1,
        expected_delivery_date=timezone.now() + timedelta(days=2),
        delivery_instructions='Leave at front door if no answer'
    )
    
    parcel2 = Parcel.objects.create(
        customer=customer2,
        pickup_address='456 Oak Ave, City, State 12346',
        delivery_address='321 Elm St, Third City, State 98765',
        recipient_name='David Lee',
        recipient_phone='+1234567896',
        description='Books and Documents',
        weight=1.2,
        dimensions='30 x 25 x 10',
        status='out_for_delivery',
        current_driver=driver2,
        expected_delivery_date=timezone.now() + timedelta(days=1),
        delivery_instructions='Ring doorbell'
    )
    
    parcel3 = Parcel.objects.create(
        customer=customer1,
        pickup_address='123 Main St, City, State 12345',
        delivery_address='555 Maple Dr, Fourth City, State 11111',
        recipient_name='Emma Davis',
        recipient_phone='+1234567897',
        description='Clothing Package',
        weight=0.8,
        dimensions='25 x 20 x 8',
        status='order_placed',
        expected_delivery_date=timezone.now() + timedelta(days=3)
    )
    
    # Create tracking events
    TrackingEvent.objects.create(
        parcel=parcel1,
        timestamp=timezone.now() - timedelta(hours=24),
        status_update='Order placed',
        notes='Parcel booking confirmed',
        created_by=customer1
    )
    
    TrackingEvent.objects.create(
        parcel=parcel1,
        timestamp=timezone.now() - timedelta(hours=20),
        status_update='Collected from sender',
        notes='Parcel collected and scanned by driver',
        location='123 Main St, City, State',
        created_by=driver_user1
    )
    
    TrackingEvent.objects.create(
        parcel=parcel1,
        timestamp=timezone.now() - timedelta(hours=18),
        status_update='In transit',
        notes='Parcel is on the way to destination',
        location='Highway 101, Mile 45',
        created_by=driver_user1
    )
    
    TrackingEvent.objects.create(
        parcel=parcel2,
        timestamp=timezone.now() - timedelta(hours=12),
        status_update='Order placed',
        notes='Parcel booking confirmed',
        created_by=customer2
    )
    
    TrackingEvent.objects.create(
        parcel=parcel2,
        timestamp=timezone.now() - timedelta(hours=8),
        status_update='Collected from sender',
        notes='Parcel collected and scanned by driver',
        location='456 Oak Ave, City, State',
        created_by=driver_user2
    )
    
    TrackingEvent.objects.create(
        parcel=parcel2,
        timestamp=timezone.now() - timedelta(hours=2),
        status_update='Out for delivery',
        notes='Parcel is out for delivery',
        location='Third City Distribution Center',
        created_by=driver_user2
    )
    
    TrackingEvent.objects.create(
        parcel=parcel3,
        timestamp=timezone.now() - timedelta(hours=6),
        status_update='Order placed',
        notes='Parcel booking confirmed',
        created_by=customer1
    )
    
    # Create jobs
    Job.objects.create(
        parcel=parcel1,
        driver=driver1,
        job_type='pickup',
        status='completed',
        assigned_at=timezone.now() - timedelta(hours=25),
        accepted_at=timezone.now() - timedelta(hours=24),
        completed_at=timezone.now() - timedelta(hours=20)
    )
    
    Job.objects.create(
        parcel=parcel1,
        driver=driver1,
        job_type='delivery',
        status='en_route',
        assigned_at=timezone.now() - timedelta(hours=19),
        accepted_at=timezone.now() - timedelta(hours=18)
    )
    
    Job.objects.create(
        parcel=parcel2,
        driver=driver2,
        job_type='pickup',
        status='completed',
        assigned_at=timezone.now() - timedelta(hours=13),
        accepted_at=timezone.now() - timedelta(hours=12),
        completed_at=timezone.now() - timedelta(hours=8)
    )
    
    Job.objects.create(
        parcel=parcel2,
        driver=driver2,
        job_type='delivery',
        status='en_route',
        assigned_at=timezone.now() - timedelta(hours=7),
        accepted_at=timezone.now() - timedelta(hours=6)
    )
    
    Job.objects.create(
        parcel=parcel3,
        driver=driver1,
        job_type='pickup',
        status='assigned',
        assigned_at=timezone.now() - timedelta(hours=1)
    )
    
    # Create notifications
    Notification.objects.create(
        user=customer1,
        title='Parcel Collected',
        message=f'Your parcel {parcel1.tracking_number} has been collected and is on its way.',
        parcel=parcel1,
        created_at=timezone.now() - timedelta(hours=20)
    )
    
    Notification.objects.create(
        user=customer2,
        title='Out for Delivery',
        message=f'Your parcel {parcel2.tracking_number} is out for delivery.',
        parcel=parcel2,
        created_at=timezone.now() - timedelta(hours=2)
    )
    
    Notification.objects.create(
        user=driver_user1,
        title='New Pickup Job',
        message=f'You have been assigned a pickup job for parcel {parcel3.tracking_number}.',
        parcel=parcel3,
        created_at=timezone.now() - timedelta(hours=1)
    )
    
    print("Test data created successfully!")
    print(f"Created {User.objects.count()} users")
    print(f"Created {Parcel.objects.count()} parcels")
    print(f"Created {TrackingEvent.objects.count()} tracking events")
    print(f"Created {Job.objects.count()} jobs")
    print(f"Created {Notification.objects.count()} notifications")
    
    print("\nTest accounts:")
    print("Customer 1: username=customer1, password=password123")
    print("Customer 2: username=customer2, password=password123")
    print("Controller: username=controller1, password=password123")
    print("Driver 1: username=driver1, password=password123")
    print("Driver 2: username=driver2, password=password123")
    print("Admin: username=admin, password=admin123")

if __name__ == '__main__':
    create_test_data()

