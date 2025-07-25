from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from .forms import ParcelUpdateForm,JobUpdateForm, ParcelForm
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib import messages
import barcode
from barcode.writer import ImageWriter
import random
import string
from .models import Parcel
from .models import User, Driver, Parcel, TrackingEvent, Job, Notification, AboutSection
from .serializers import (
    UserSerializer, LoginSerializer, DriverSerializer, ParcelSerializer,
    ParcelBookingSerializer, JobSerializer, NotificationSerializer,
    ParcelTrackingSerializer, DriverLocationUpdateSerializer,
    DeliveryCompletionSerializer, TrackingEventSerializer
)

#website views
 

def about_page(request):
    about = AboutSection.objects.first()
    return render(request, 'tracking/about.html', {'about': about})



# Authentication Views
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'})





from django.urls import reverse
from rest_framework.response import Response
from rest_framework import status

class ParcelBookingView(generics.CreateAPIView):
    serializer_class = ParcelBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        parcel = serializer.save()

        # Create initial tracking event
        TrackingEvent.objects.create(
            parcel=parcel,
            status_update='Order placed',
            notes='Parcel booking confirmed',
            created_by=self.request.user
        )

        # Create notification for customer
        Notification.objects.create(
            user=parcel.customer,
            title='Parcel Booked Successfully',
            message=f'Your parcel with tracking number {parcel.tracking_number} has been booked.',
            parcel=parcel
        )

        # Store parcel for use in `create` response
        self.parcel = parcel

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        parcel = getattr(self, 'parcel', None)
        if parcel:
            response.data.update({
                'message': 'Parcel booked successfully!',
                'tracking_number': parcel.tracking_number,
                'parcel_id': parcel.id,
                'label_url': reverse('print_label', args=[parcel.id])
            })
        return response


# Customer Views

# class ParcelBookingView(generics.CreateAPIView):
#     serializer_class = ParcelBookingSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def perform_create(self, serializer):
#         parcel = serializer.save()
#         # Create initial tracking event
#         TrackingEvent.objects.create(
#             parcel=parcel,
#             status_update='Order placed',
#             notes='Parcel booking confirmed',
#             created_by=self.request.user
#         )
#         # Create notification for customer
#         Notification.objects.create(
#             user=parcel.customer,
#             title='Parcel Booked Successfully',
#             message=f'Your parcel with tracking number {parcel.tracking_number} has been booked.',
#             parcel=parcel
#         )


class CustomerParcelsView(generics.ListAPIView):
    serializer_class = ParcelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Parcel.objects.filter(customer=self.request.user)


class ParcelDetailView(generics.RetrieveAPIView):
    serializer_class = ParcelSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'tracking_number'

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'customer':
            return Parcel.objects.filter(customer=user, can_customer_track=True)
        elif user.user_type in ['controller', 'driver']:
            return Parcel.objects.all()
        return Parcel.objects.none()


# Public Tracking View
class PublicTrackingView(generics.RetrieveAPIView):
    serializer_class = ParcelTrackingSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'tracking_number'
    queryset = Parcel.objects.all()


    def get_queryset(self):
        return Parcel.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if not instance.can_customer_track:
            return Response({
                'error': 'Tracking is not available for this parcel yet.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

# Controller Views
class AllParcelsView(generics.ListAPIView):
    serializer_class = ParcelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type == 'controller':
            return Parcel.objects.all()
        return Parcel.objects.none()


class AllDriversView(generics.ListAPIView):
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type == 'controller':
            return Driver.objects.all()
        return Driver.objects.none()


class AssignDriverView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, parcel_id):
        if request.user.user_type != 'controller':
            return Response({'error': 'Only controllers can assign drivers'}, 
                          status=status.HTTP_403_FORBIDDEN)

        parcel = get_object_or_404(Parcel, id=parcel_id)
        driver_id = request.data.get('driver_id')
        job_type = request.data.get('job_type', 'pickup')

        if not driver_id:
            return Response({'error': 'Driver ID is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        driver = get_object_or_404(Driver, pk=driver_id)

        # Create job
        job = Job.objects.create(
            parcel=parcel,
            driver=driver,
            job_type=job_type
        )

        # Update parcel status
        if job_type == 'pickup':
            parcel.status = 'awaiting_pickup'
        else:
            parcel.status = 'out_for_delivery'
            parcel.can_customer_track = True  # ✅ Allow customer to track now

        parcel.current_driver = driver
        parcel.save()

        # Create tracking event
        TrackingEvent.objects.create(
            parcel=parcel,
            status_update=f'Assigned to driver for {job_type}',
            notes=f'Driver {driver.user.username} assigned for {job_type}',
            created_by=request.user
        )

        # Create notification for driver
        Notification.objects.create(
            user=driver.user,
            title=f'New {job_type.title()} Job Assigned',
            message=f'You have been assigned a {job_type} job for parcel {parcel.tracking_number}',
            parcel=parcel
        )

        return Response({'message': 'Driver assigned successfully', 'job_id': job.id})


# Driver Views
class DriverJobsView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type == 'driver':
            try:
                driver = Driver.objects.get(user=self.request.user)
                return Job.objects.filter(driver=driver)
            except Driver.DoesNotExist:
                return Job.objects.none()
        return Job.objects.none()


class AcceptJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id):
        if request.user.user_type != 'driver':
            return Response({'error': 'Only drivers can accept jobs'}, 
                          status=status.HTTP_403_FORBIDDEN)

        job = get_object_or_404(Job, id=job_id)
        
        if job.driver.user != request.user:
            return Response({'error': 'You can only accept your own jobs'}, 
                          status=status.HTTP_403_FORBIDDEN)

        job.status = 'accepted'
        job.accepted_at = timezone.now()
        job.save()

        # Create tracking event
        TrackingEvent.objects.create(
            parcel=job.parcel,
            status_update=f'Driver accepted {job.job_type} job',
            notes=f'Driver {request.user.username} accepted the job',
            created_by=request.user
        )

        return Response({'message': 'Job accepted successfully'})


class ScanParcelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id):
        if request.user.user_type != 'driver':
            return Response({'error': 'Only drivers can scan parcels'}, 
                          status=status.HTTP_403_FORBIDDEN)

        job = get_object_or_404(Job, id=job_id)
        
        if job.driver.user != request.user:
            return Response({'error': 'You can only scan parcels for your own jobs'}, 
                          status=status.HTTP_403_FORBIDDEN)

        # Update job status
        job.status = 'en_route'
        job.save()

        # Update parcel status
        if job.job_type == 'pickup':
            job.parcel.status = 'collected'
            status_message = 'Parcel collected and scanned'
        else:
            job.parcel.status = 'out_for_delivery'
            job.parcel.can_customer_track = True  # ✅ Allow customer to track now
            status_message = 'Parcel scanned for delivery'
        
        job.parcel.save()

        

        # Create tracking event
        TrackingEvent.objects.create(
            parcel=job.parcel,
            status_update=status_message,
            notes=f'Parcel scanned by driver {request.user.username}',
            created_by=request.user
        )

        # Create notification for customer
        Notification.objects.create(
            user=job.parcel.customer,
            title='Parcel Status Update',
            message=f'Your parcel {job.parcel.tracking_number} has been {status_message.lower()}',
            parcel=job.parcel
        )

        return Response({'message': 'Parcel scanned successfully'})


class UpdateLocationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.user_type != 'driver':
            return Response({'error': 'Only drivers can update location'}, 
                          status=status.HTTP_403_FORBIDDEN)

        serializer = DriverLocationUpdateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                driver = Driver.objects.get(user=request.user)
                driver.current_latitude = serializer.validated_data['latitude']
                driver.current_longitude = serializer.validated_data['longitude']
                driver.save()
                return Response({'message': 'Location updated successfully'})
            except Driver.DoesNotExist:
                return Response({'error': 'Driver profile not found'}, 
                              status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteDeliveryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id):
        if request.user.user_type != 'driver':
            return Response({'error': 'Only drivers can complete deliveries'}, 
                          status=status.HTTP_403_FORBIDDEN)

        job = get_object_or_404(Job, id=job_id)
        
        if job.driver.user != request.user:
            return Response({'error': 'You can only complete your own jobs'}, 
                          status=status.HTTP_403_FORBIDDEN)

        serializer = DeliveryCompletionSerializer(data=request.data)
        if serializer.is_valid():
            # Update job
            job.status = 'completed'
            job.completed_at = timezone.now()
            job.notes = serializer.validated_data.get('notes', '')
            job.save()

            # Update parcel
            job.parcel.status = 'delivered'
            job.parcel.save()

            # Create tracking event with proof
            tracking_event = TrackingEvent.objects.create(
                parcel=job.parcel,
                status_update='Delivered successfully',
                notes=serializer.validated_data.get('notes', 'Package delivered'),
                created_by=request.user
            )

            # Add delivery proof if provided
            if 'delivery_image' in serializer.validated_data:
                tracking_event.image = serializer.validated_data['delivery_image']
            if 'signature' in serializer.validated_data:
                tracking_event.signature = serializer.validated_data['signature']
            tracking_event.save()

            # Create notification for customer
            Notification.objects.create(
                user=job.parcel.customer,
                title='Parcel Delivered',
                message=f'Your parcel {job.parcel.tracking_number} has been delivered successfully',
                parcel=job.parcel
            )

            return Response({'message': 'Delivery completed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Notification Views
class NotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read'})



# Web Interface Views
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def home_view(request):
    return render(request, 'tracking/home.html')

def home1_view(request):
    return render(request, 'tracking/index.html')

def services_page(request):
    return render(request, 'tracking/service.html')

def about_view(request):
    about = AboutSection.objects.first()
    return render(request, 'tracking/about.html', {'about': about})


def login_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'tracking/login.html')


def register_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'tracking/register.html')


def logout_page(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')



def track_parcel_page(request):
    tracking_number = request.GET.get('tracking_number')
    parcel = None

    if tracking_number:
        try:
            parcel = Parcel.objects.get(tracking_number=tracking_number)
        except Parcel.DoesNotExist:
            parcel = None

    return render(request, 'tracking/track_parcel.html', {
        'parcel': parcel
    })

import uuid


@login_required
def book_parcel_page(request):
    if request.user.user_type != 'customer':
        return redirect('home')

    if request.method == 'POST':
        form = ParcelForm(request.POST)
        if form.is_valid():
            parcel = form.save(commit=False)
            parcel.customer = request.user
            parcel.tracking_number = str(uuid.uuid4()).replace('-', '')[:10]
            parcel.save()
        return redirect('print_label', parcel_id=parcel.id)
    else:
        form = ParcelForm()

    return render(request, 'tracking/book_parcel.html', {'form': form})


def print_label(request, parcel_id):
    parcel = get_object_or_404(Parcel, id=parcel_id)
    return render(request, 'tracking/label.html', {'parcel': parcel})
# @login_required
# def print_label(request, parcel_id):
#     parcel = get_object_or_404(Parcel, id=parcel_id)
#     return render(request, 'tracking/label.html', {'parcel': parcel})

@login_required
def my_parcels_page(request):
    if request.user.user_type != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('home')
    return render(request, 'tracking/my_parcels.html')


# @login_required
# def admin_dashboard_page(request):
#     if request.user.user_type != 'controller':
#         messages.error(request, 'Access denied.')
#         return redirect('home')
#     return render(request, 'tracking/admin_dashboard.html')


@login_required
def driver_dashboard_page(request):
    if request.user.user_type != 'driver':
        messages.error(request, 'Access denied.')
        return redirect('home')
    return render(request, 'tracking/driver_dashboard.html')


@login_required
def profile_page(request):
    return render(request, 'tracking/profile.html')


# @login_required
# def admin_dashboard_page(request):
#     if request.user.user_type != 'controller':
#         messages.error(request, 'Access denied.')
#         return redirect('home')

#     # 🟢 Send all parcels to the template
#     parcels = Parcel.objects.select_related('customer', 'current_driver__user').all()

#     return render(request, 'tracking/admin_dashboard.html', {
#         'parcels': parcels
#     })

@login_required
def admin_dashboard_page(request):
    if request.user.user_type != 'controller':
        messages.error(request, 'Access denied.')
        return redirect('home')

    from .models import Parcel, Job, Driver

    parcels = Parcel.objects.select_related('customer', 'current_driver__user').all()
    jobs = Job.objects.select_related('driver', 'parcel').all()
    drivers = Driver.objects.select_related('user').all()

   

    context = {
        'total_parcels': parcels.count(),
        'pending_parcels': parcels.filter(status__in=['order_placed', 'awaiting_pickup']).count(),
        'in_transit_parcels': parcels.filter(status__in=['collected', 'in_transit', 'out_for_delivery']).count(),
        'delivered_parcels': parcels.filter(status='delivered').count(),
        'total_jobs': jobs.count(),
        'parcels': parcels,
        'jobs': jobs,
        'drivers': drivers,
    }

    return render(request, 'tracking/admin_dashboard.html', context)



def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        full_message = f"From: {name}\nEmail: {email}\n\nMessage:\n{message}"

        # Route complaints to the complaint email
        if "complaint" in subject.lower():
            recipient = "Complaints@fjwlogistics247.co.uk"
        else:
            recipient = "Admin@fjwlogistics247.co.uk"

        try:
            send_mail(
                subject,
                full_message,
                "Admin@fjwlogistics247.co.uk",  # From email
                [recipient],
                fail_silently=False,
            )
            messages.success(request, "Your message was sent successfully!")
        except Exception as e:
            messages.error(request, f"Failed to send message: {str(e)}")

    return render(request, "tracking/contact.html")




def generate_label(request):
    if request.method == "POST":
        name = request.POST.get("name")
        pickup = request.POST.get("pickup_address")
        delivery = request.POST.get("delivery_address")

        tracking_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        context = {
            "name": name,
            "pickup": pickup,
            "delivery": delivery,
            "tracking_id": tracking_id
        }

        return render(request, "tracking/label.html", context)

    return render(request, "tracking/form.html")


    
  

from django.shortcuts import render
from .models import Job  # Make sure Job is your parcel model

# def admin_dashboard(request):
#     total_parcels = Job.objects.count()
#     pending_parcels = Job.objects.filter(status='Pending').count()
#     in_transit_parcels = Job.objects.filter(status='In Transit').count()
#     delivered_parcels = Job.objects.filter(status='Delivered').count()

#     context = {
#         'total_parcels': total_parcels,
#         'pending_parcels': pending_parcels,
#         'in_transit_parcels': in_transit_parcels,
#         'delivered_parcels': delivered_parcels,
#     }
#     return render(request, 'tracking/dashboard.html', context)

def update_parcel_admin(request, parcel_id):
    if request.user.user_type != 'controller':
        messages.error(request, 'Access denied.')
        return redirect('home')

    parcel = get_object_or_404(Parcel, id=parcel_id)

    if request.method == 'POST':
        form = ParcelUpdateForm(request.POST, instance=parcel)
        if form.is_valid():
            form.save()
            messages.success(request, 'Parcel updated successfully.')
            return redirect('admin_dashboard_page')
    else:
        form = ParcelUpdateForm(instance=parcel)

    return render(request, 'tracking/update_parcel.html', {'form': form, 'parcel': parcel})



   
def delete_parcel_admin(request, parcel_id):
    if request.user.user_type != 'controller':
        messages.error(request, 'Access denied.')
        return redirect('home')

    parcel = get_object_or_404(Parcel, id=parcel_id)
    parcel.delete()
    messages.success(request, 'Parcel deleted successfully.')
    return redirect('admin_dashboard_page')


# update_job_inline
@login_required
def update_job_inline(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == "POST":
        form = JobUpdateForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

class DriverSimulatorView(View):
    """
    Driver location simulator for testing real-time tracking functionality
    """
    def get(self, request):
        # Only allow admin users to access the simulator
        if not request.user.is_authenticated or request.user.user_type != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('login')
        
        return render(request, 'tracking/driver_simulator.html')



# Live Tracking Dashboard View
def live_tracking_dashboard(request):
    """Live driver tracking dashboard for admin users"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    
    if request.user.user_type not in ['controller', 'admin']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    context = {
        'user': request.user,
        'page_title': 'Live Driver Tracking Dashboard'
    }
    
    return render(request, 'tracking/live_tracking_dashboard.html', context)


# Enhanced Admin Dashboard View
def enhanced_admin_dashboard(request):
    """Enhanced admin dashboard with live tracking integration"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    
    if request.user.user_type not in ['controller', 'admin']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get dashboard statistics
    today = timezone.now().date()
    
    # Driver statistics
    total_drivers = Driver.objects.count()
    active_drivers = Driver.objects.filter(is_active=True).count()
    available_drivers = Driver.objects.filter(is_available=True, is_active=True).count()
    
    # Job statistics
    total_jobs_today = Job.objects.filter(assigned_at__date=today).count()
    completed_jobs_today = Job.objects.filter(
        assigned_at__date=today,
        status='completed'
    ).count()
    active_jobs = Job.objects.filter(
        status__in=['assigned', 'accepted', 'en_route']
    ).count()
    
    # Parcel statistics
    total_parcels_today = Parcel.objects.filter(booked_at__date=today).count()
    delivered_parcels_today = Parcel.objects.filter(
        booked_at__date=today,
        status='delivered'
    ).count()
    in_transit_parcels = Parcel.objects.filter(
        status__in=['collected', 'in_transit', 'out_for_delivery']
    ).count()
    
    # Recent activities
    recent_parcels = Parcel.objects.order_by('-booked_at')[:10]
    recent_jobs = Job.objects.select_related('driver__user', 'parcel').order_by('-assigned_at')[:10]
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'user': request.user,
        'page_title': 'Enhanced Admin Dashboard',
        'statistics': {
            'drivers': {
                'total': total_drivers,
                'active': active_drivers,
                'available': available_drivers,
                'utilization_rate': round((active_drivers / total_drivers * 100), 2) if total_drivers > 0 else 0
            },
            'jobs': {
                'total_today': total_jobs_today,
                'completed_today': completed_jobs_today,
                'active': active_jobs,
                'completion_rate': round((completed_jobs_today / total_jobs_today * 100), 2) if total_jobs_today > 0 else 0
            },
            'parcels': {
                'total_today': total_parcels_today,
                'delivered_today': delivered_parcels_today,
                'in_transit': in_transit_parcels,
                'delivery_rate': round((delivered_parcels_today / total_parcels_today * 100), 2) if total_parcels_today > 0 else 0
            }
        },
        'recent_parcels': recent_parcels,
        'recent_jobs': recent_jobs,
        'recent_notifications': recent_notifications,
        'today': today
    }
    
    return render(request, 'tracking/enhanced_admin_dashboard.html', context)


# Driver Management Views
def driver_management(request):
    """Driver management interface for admin users"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    
    if request.user.user_type not in ['controller', 'admin']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    drivers = Driver.objects.select_related('user').all()
    
    context = {
        'user': request.user,
        'page_title': 'Driver Management',
        'drivers': drivers
    }
    
    return render(request, 'tracking/driver_management.html', context)


# Route Management Views
def route_management(request):
    """Route management interface for admin users"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    
    if request.user.user_type not in ['controller', 'admin']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    from .models import Route
    routes = Route.objects.select_related('driver__user').all()
    
    context = {
        'user': request.user,
        'page_title': 'Route Management',
        'routes': routes
    }
    
    return render(request, 'tracking/route_management.html', context)


# Parcel Tracking Management
def parcel_tracking_management(request):
    """Enhanced parcel tracking management for admin users"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    
    if request.user.user_type not in ['controller', 'admin']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    driver_filter = request.GET.get('driver', '')
    
    # Base queryset
    parcels = Parcel.objects.select_related('customer', 'current_driver__user').all()
    
    # Apply filters
    if status_filter:
        parcels = parcels.filter(status=status_filter)
    
    if date_filter:
        parcels = parcels.filter(booked_at__date=date_filter)
    
    if driver_filter:
        parcels = parcels.filter(current_driver_id=driver_filter)
    
    # Order by most recent
    parcels = parcels.order_by('-booked_at')
    
    # Get filter options
    drivers = Driver.objects.select_related('user').all()
    status_choices = Parcel.STATUS_CHOICES
    
    context = {
        'user': request.user,
        'page_title': 'Parcel Tracking Management',
        'parcels': parcels,
        'drivers': drivers,
        'status_choices': status_choices,
        'current_filters': {
            'status': status_filter,
            'date': date_filter,
            'driver': driver_filter
        }
    }
    
    return render(request, 'tracking/parcel_tracking_management.html', context)


# Analytics and Reports
def tracking_analytics(request):
    """Analytics and reports dashboard for admin users"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    
    if request.user.user_type not in ['controller', 'admin']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    from .models import DriverLocationHistory
    from django.db.models import Count, Avg
    from datetime import timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Performance metrics
    performance_data = {
        'daily_deliveries': Parcel.objects.filter(
            status='delivered',
            booked_at__date=today
        ).count(),
        'weekly_deliveries': Parcel.objects.filter(
            status='delivered',
            booked_at__date__gte=week_ago
        ).count(),
        'monthly_deliveries': Parcel.objects.filter(
            status='delivered',
            booked_at__date__gte=month_ago
        ).count(),
        'average_delivery_time': Job.objects.filter(
            status='completed',
            completed_at__date__gte=week_ago
        ).aggregate(
            avg_time=Avg('completed_at') - Avg('assigned_at')
        )['avg_time'],
        'driver_utilization': Driver.objects.filter(
            is_active=True
        ).count() / Driver.objects.count() * 100 if Driver.objects.count() > 0 else 0
    }
    
    # Location tracking statistics
    location_stats = {
        'total_updates_today': DriverLocationHistory.objects.filter(
            timestamp__date=today
        ).count(),
        'active_drivers_today': DriverLocationHistory.objects.filter(
            timestamp__date=today
        ).values('driver').distinct().count(),
        'average_updates_per_driver': DriverLocationHistory.objects.filter(
            timestamp__date=today
        ).count() / Driver.objects.filter(is_active=True).count() if Driver.objects.filter(is_active=True).count() > 0 else 0
    }
    
    context = {
        'user': request.user,
        'page_title': 'Tracking Analytics',
        'performance_data': performance_data,
        'location_stats': location_stats,
        'today': today
    }
    
    return render(request, 'tracking/tracking_analytics.html', context)



# Enhanced Parcel Tracking Views
def enhanced_parcel_tracking(request):
    """Enhanced parcel tracking interface for customers"""
    context = {
        'page_title': 'Track Your Parcel'
    }
    return render(request, 'tracking/enhanced_parcel_tracking.html', context)


def delivery_management_dashboard(request):
    """Delivery management dashboard for drivers"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    
    if request.user.user_type != 'driver':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    try:
        driver = Driver.objects.get(user=request.user)
    except Driver.DoesNotExist:
        messages.error(request, 'Driver profile not found.')
        return redirect('home')
    
    # Get driver's jobs
    jobs = Job.objects.filter(driver=driver).select_related('parcel').order_by('-assigned_at')
    
    # Get performance statistics
    today = timezone.now().date()
    completed_jobs_today = jobs.filter(
        status='completed',
        completed_at__date=today
    ).count()
    
    pending_jobs = jobs.filter(
        status__in=['assigned', 'accepted', 'en_route']
    ).count()
    
    context = {
        'user': request.user,
        'driver': driver,
        'jobs': jobs,
        'page_title': 'Delivery Management',
        'stats': {
            'completed_jobs': completed_jobs_today,
            'pending_jobs': pending_jobs,
            'total_distance': driver.total_distance_today,
            'efficiency': 85  # Calculate based on actual metrics
        }
    }
    
    return render(request, 'tracking/delivery_management.html', context)


# Enhanced Delivery Features API Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_job_route(request, job_id):
    """Start a job route and begin tracking"""
    if request.user.user_type != 'driver':
        return Response(
            {'error': 'Only drivers can start routes'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        driver = Driver.objects.get(user=request.user)
        job = get_object_or_404(Job, id=job_id, driver=driver)
        
        if job.status != 'accepted':
            return Response(
                {'error': 'Job must be accepted before starting route'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update job status
        job.status = 'en_route'
        job.route_started_at = timezone.now()
        job.save()
        
        # Create tracking event
        TrackingEvent.objects.create(
            parcel=job.parcel,
            status_update=f'Driver started route for {job.job_type}',
            location='En route',
            created_by=request.user
        )
        
        # Update parcel status
        if job.job_type == 'pickup':
            job.parcel.status = 'collected'
        else:
            job.parcel.status = 'out_for_delivery'
        job.parcel.save()
        
        return Response({
            'message': 'Route started successfully',
            'job_id': job.id,
            'status': job.status,
            'timestamp': timezone.now().isoformat()
        })
        
    except Driver.DoesNotExist:
        return Response(
            {'error': 'Driver profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to start route: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def complete_delivery_enhanced(request, job_id):
    """Complete a delivery with enhanced features"""
    if request.user.user_type != 'driver':
        return Response(
            {'error': 'Only drivers can complete deliveries'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        driver = Driver.objects.get(user=request.user)
        job = get_object_or_404(Job, id=job_id, driver=driver)
        
        if job.status != 'en_route':
            return Response(
                {'error': 'Job must be en route before completion'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get completion data
        completion_notes = request.data.get('notes', '')
        signature_data = request.data.get('signature')
        photo_data = request.data.get('photo')
        delivery_location = request.data.get('location', '')
        
        # Update job status
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.route_completed_at = timezone.now()
        job.notes = completion_notes
        job.save()
        
        # Create completion tracking event
        tracking_event = TrackingEvent.objects.create(
            parcel=job.parcel,
            status_update='Delivery completed',
            location=delivery_location or 'Delivered',
            notes=completion_notes,
            created_by=request.user
        )
        
        # Handle signature and photo uploads
        if signature_data:
            # Process signature data (base64 to image)
            pass  # Implementation would handle file upload
            
        if photo_data:
            # Process photo data
            pass  # Implementation would handle file upload
        
        # Update parcel status
        job.parcel.status = 'delivered'
        job.parcel.save()
        
        # Send notification to customer
        Notification.objects.create(
            user=job.parcel.customer,
            title='Parcel Delivered',
            message=f'Your parcel #{job.parcel.tracking_number} has been delivered successfully.',
            parcel=job.parcel
        )
        
        # Update driver performance
        driver.total_distance_today += job.actual_distance or 0
        driver.save()
        
        return Response({
            'message': 'Delivery completed successfully',
            'job_id': job.id,
            'tracking_number': job.parcel.tracking_number,
            'completed_at': job.completed_at.isoformat()
        })
        
    except Driver.DoesNotExist:
        return Response(
            {'error': 'Driver profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to complete delivery: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def report_delivery_issue(request, job_id):
    """Report an issue with delivery"""
    if request.user.user_type != 'driver':
        return Response(
            {'error': 'Only drivers can report issues'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        driver = Driver.objects.get(user=request.user)
        job = get_object_or_404(Job, id=job_id, driver=driver)
        
        issue_type = request.data.get('issue_type')
        issue_description = request.data.get('description')
        
        if not issue_type or not issue_description:
            return Response(
                {'error': 'Issue type and description are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create tracking event for the issue
        TrackingEvent.objects.create(
            parcel=job.parcel,
            status_update=f'Delivery issue reported: {issue_type}',
            location=request.data.get('location', ''),
            notes=issue_description,
            created_by=request.user
        )
        
        # Update job status if needed
        if issue_type in ['failed_delivery', 'customer_unavailable']:
            job.status = 'failed'
            job.parcel.status = 'failed_delivery'
            job.parcel.save()
            job.save()
        
        # Create notification for admin
        admin_users = User.objects.filter(user_type='controller')
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                title=f'Delivery Issue Reported',
                message=f'Driver {driver.user.username} reported an issue with parcel #{job.parcel.tracking_number}: {issue_type}',
                parcel=job.parcel
            )
        
        return Response({
            'message': 'Issue reported successfully',
            'job_id': job.id,
            'issue_type': issue_type,
            'timestamp': timezone.now().isoformat()
        })
        
    except Driver.DoesNotExist:
        return Response(
            {'error': 'Driver profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to report issue: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_driver_performance(request):
    """Get driver performance statistics"""
    if request.user.user_type != 'driver':
        return Response(
            {'error': 'Only drivers can access performance data'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        driver = Driver.objects.get(user=request.user)
        today = timezone.now().date()
        
        # Get job statistics
        jobs_today = Job.objects.filter(driver=driver, assigned_at__date=today)
        completed_jobs = jobs_today.filter(status='completed').count()
        pending_jobs = jobs_today.filter(status__in=['assigned', 'accepted', 'en_route']).count()
        total_jobs = jobs_today.count()
        
        # Calculate efficiency
        efficiency = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        # Get distance data
        total_distance = driver.total_distance_today
        
        # Get location update statistics
        location_updates_today = DriverLocationHistory.objects.filter(
            driver=driver,
            timestamp__date=today
        ).count()
        
        performance_data = {
            'completed_jobs': completed_jobs,
            'pending_jobs': pending_jobs,
            'total_jobs': total_jobs,
            'efficiency': round(efficiency, 1),
            'total_distance': total_distance,
            'location_updates': location_updates_today,
            'last_location_update': driver.last_location_update.isoformat() if driver.last_location_update else None,
            'is_active': driver.is_active,
            'is_available': driver.is_available
        }
        
        return Response(performance_data)
        
    except Driver.DoesNotExist:
        return Response(
            {'error': 'Driver profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to get performance data: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def enable_customer_tracking_enhanced(request, job_id):
    """Enable enhanced customer tracking for a job"""
    if request.user.user_type not in ['controller', 'admin', 'driver']:
        return Response(
            {'error': 'Insufficient permissions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        job = get_object_or_404(Job, id=job_id)
        
        # Enable customer tracking
        job.customer_tracking_enabled = True
        job.tracking_start_time = timezone.now()
        job.parcel.can_customer_track = True
        
        # Set tracking end time (e.g., 24 hours from now)
        job.tracking_end_time = timezone.now() + timezone.timedelta(hours=24)
        
        job.save()
        job.parcel.save()
        
        # Create notification for customer
        Notification.objects.create(
            user=job.parcel.customer,
            title='Live Tracking Enabled',
            message=f'Live tracking is now available for your parcel #{job.parcel.tracking_number}. You can track your delivery in real-time.',
            parcel=job.parcel
        )
        
        return Response({
            'message': 'Customer tracking enabled successfully',
            'job_id': job.id,
            'tracking_number': job.parcel.tracking_number,
            'tracking_enabled': True,
            'tracking_start_time': job.tracking_start_time.isoformat(),
            'tracking_end_time': job.tracking_end_time.isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to enable customer tracking: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

