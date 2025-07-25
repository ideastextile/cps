"""
API views for real-time driver tracking and location management
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from .models import Driver, Job, Parcel, DriverLocationHistory, Route
from .services import LocationTrackingService, GoogleMapsService
from .serializers import DriverLocationUpdateSerializer


class DriverLocationUpdateAPIView(APIView):
    """API endpoint for drivers to update their location"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if request.user.user_type != 'driver':
            return Response(
                {'error': 'Only drivers can update location'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            driver = Driver.objects.get(user=request.user)
        except Driver.DoesNotExist:
            return Response(
                {'error': 'Driver profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = DriverLocationUpdateSerializer(data=request.data)
        if serializer.is_valid():
            success = LocationTrackingService.update_driver_location(
                driver=driver,
                latitude=serializer.validated_data['latitude'],
                longitude=serializer.validated_data['longitude'],
                accuracy=serializer.validated_data.get('accuracy'),
                speed=serializer.validated_data.get('speed'),
                heading=serializer.validated_data.get('heading')
            )
            
            if success:
                return Response({
                    'message': 'Location updated successfully',
                    'timestamp': timezone.now().isoformat()
                })
            else:
                return Response(
                    {'error': 'Failed to update location'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminDriverLocationsAPIView(APIView):
    """API endpoint for admin to get all active driver locations"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.user_type != 'controller':
            return Response(
                {'error': 'Only controllers can access driver locations'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        driver_locations = LocationTrackingService.get_active_drivers_locations()
        return Response({
            'drivers': driver_locations,
            'timestamp': timezone.now().isoformat(),
            'total_active_drivers': len(driver_locations)
        })


class DriverRouteHistoryAPIView(APIView):
    """API endpoint to get driver's route history"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, driver_id):
        if request.user.user_type not in ['controller', 'driver']:
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Drivers can only access their own route history
        if request.user.user_type == 'driver':
            try:
                driver = Driver.objects.get(user=request.user)
                if driver.pk != int(driver_id):
                    return Response(
                        {'error': 'You can only access your own route history'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except (Driver.DoesNotExist, ValueError):
                return Response(
                    {'error': 'Driver not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        driver = get_object_or_404(Driver, pk=driver_id)
        hours = int(request.GET.get('hours', 24))
        
        route_history = LocationTrackingService.get_driver_route_history(driver, hours)
        
        return Response({
            'driver_id': driver_id,
            'driver_name': driver.user.username,
            'route_history': route_history,
            'hours_back': hours,
            'total_points': len(route_history)
        })


class CustomerTrackingAPIView(APIView):
    """API endpoint for customers to track their parcel's driver location"""
    permission_classes = [permissions.AllowAny]  # Allow public access with tracking number
    
    def get(self, request, tracking_number):
        try:
            parcel = Parcel.objects.get(tracking_number=tracking_number)
        except Parcel.DoesNotExist:
            return Response(
                {'error': 'Parcel not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if customer tracking is enabled
        if not parcel.can_customer_track:
            return Response(
                {'error': 'Tracking is not available for this parcel yet'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get current active job for this parcel
        current_job = parcel.jobs.filter(
            status__in=['accepted', 'en_route'],
            customer_tracking_enabled=True
        ).first()
        
        if not current_job or not current_job.driver:
            return Response({
                'tracking_available': False,
                'message': 'Driver location tracking is not currently available for this parcel'
            })
        
        driver = current_job.driver
        
        # Check if driver has recent location data
        if not driver.current_latitude or not driver.current_longitude:
            return Response({
                'tracking_available': False,
                'message': 'Driver location is not currently available'
            })
        
        # Calculate ETA if possible
        eta = None
        if parcel.delivery_address:
            maps_service = GoogleMapsService()
            delivery_coords = maps_service.geocode_address(parcel.delivery_address)
            if delivery_coords:
                eta = maps_service.calculate_eta(
                    {'lat': driver.current_latitude, 'lng': driver.current_longitude},
                    delivery_coords
                )
        
        return Response({
            'tracking_available': True,
            'parcel_tracking_number': tracking_number,
            'driver_location': {
                'latitude': driver.current_latitude,
                'longitude': driver.current_longitude,
                'last_update': driver.last_location_update,
                'accuracy': driver.location_accuracy
            },
            'job_info': {
                'job_type': current_job.job_type,
                'status': current_job.status,
                'estimated_arrival': eta.isoformat() if eta else None
            },
            'parcel_status': parcel.status
        })


class EnableCustomerTrackingAPIView(APIView):
    """API endpoint for admin to enable/disable customer tracking for a job"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, job_id):
        if request.user.user_type != 'controller':
            return Response(
                {'error': 'Only controllers can manage customer tracking'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        job = get_object_or_404(Job, id=job_id)
        enable_tracking = request.data.get('enable_tracking', False)
        
        job.customer_tracking_enabled = enable_tracking
        if enable_tracking:
            job.tracking_start_time = timezone.now()
            job.parcel.can_customer_track = True
            job.parcel.save()
        else:
            job.tracking_end_time = timezone.now()
        
        job.save()
        
        return Response({
            'message': f'Customer tracking {"enabled" if enable_tracking else "disabled"} for job {job_id}',
            'job_id': job_id,
            'tracking_enabled': enable_tracking,
            'parcel_tracking_number': job.parcel.tracking_number
        })


@method_decorator(csrf_exempt, name='dispatch')
class DriverLocationWebhookAPIView(APIView):
    """Webhook endpoint for receiving location updates from mobile apps"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if request.user.user_type != 'driver':
            return Response(
                {'error': 'Only drivers can send location updates'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            driver = Driver.objects.get(user=request.user)
        except Driver.DoesNotExist:
            return Response(
                {'error': 'Driver profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Handle batch location updates
        locations = request.data.get('locations', [])
        if not locations:
            return Response(
                {'error': 'No location data provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        successful_updates = 0
        for location_data in locations:
            try:
                success = LocationTrackingService.update_driver_location(
                    driver=driver,
                    latitude=location_data.get('latitude'),
                    longitude=location_data.get('longitude'),
                    accuracy=location_data.get('accuracy'),
                    speed=location_data.get('speed'),
                    heading=location_data.get('heading')
                )
                if success:
                    successful_updates += 1
            except Exception as e:
                continue  # Skip invalid location data
        
        return Response({
            'message': f'Processed {successful_updates} location updates',
            'total_received': len(locations),
            'successful_updates': successful_updates
        })


class RouteOptimizationAPIView(APIView):
    """API endpoint for route optimization using Google Maps"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if request.user.user_type not in ['controller', 'driver']:
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        start_address = request.data.get('start_address')
        stop_addresses = request.data.get('stop_addresses', [])
        end_address = request.data.get('end_address')
        
        if not start_address or not stop_addresses:
            return Response(
                {'error': 'Start address and stop addresses are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        maps_service = GoogleMapsService()
        
        # Geocode addresses
        start_coords = maps_service.geocode_address(start_address)
        stop_coords = [maps_service.geocode_address(addr) for addr in stop_addresses]
        end_coords = maps_service.geocode_address(end_address) if end_address else start_coords
        
        if not start_coords or not all(stop_coords):
            return Response(
                {'error': 'Failed to geocode one or more addresses'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Optimize route
        optimized_route = maps_service.optimize_route(start_coords, stop_coords, end_coords)
        
        return Response({
            'optimized_route': optimized_route,
            'start_coordinates': start_coords,
            'stop_coordinates': stop_coords,
            'end_coordinates': end_coords
        })


# Function-based API views for simpler endpoints

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_driver_status(request, driver_id):
    """Get current status of a specific driver"""
    if request.user.user_type not in ['controller', 'driver']:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    driver = get_object_or_404(Driver, pk=driver_id)
    
    # Drivers can only access their own status
    if request.user.user_type == 'driver' and driver.user != request.user:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    current_job = driver.jobs.filter(status__in=['assigned', 'accepted', 'en_route']).first()
    
    return Response({
        'driver_id': driver_id,
        'username': driver.user.username,
        'is_active': driver.is_active,
        'is_available': driver.is_available,
        'current_location': {
            'latitude': driver.current_latitude,
            'longitude': driver.current_longitude,
            'last_update': driver.last_location_update,
            'accuracy': driver.location_accuracy
        } if driver.current_latitude and driver.current_longitude else None,
        'current_job': {
            'id': current_job.id,
            'parcel_tracking': current_job.parcel.tracking_number,
            'job_type': current_job.job_type,
            'status': current_job.status,
            'customer_tracking_enabled': current_job.customer_tracking_enabled
        } if current_job else None,
        'performance': {
            'total_distance_today': driver.total_distance_today
        }
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_driver_active_status(request, driver_id):
    """Toggle driver's active status (on duty / off duty)"""
    if request.user.user_type not in ['controller', 'driver']:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    driver = get_object_or_404(Driver, pk=driver_id)
    
    # Drivers can only toggle their own status
    if request.user.user_type == 'driver' and driver.user != request.user:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    driver.is_active = not driver.is_active
    driver.save()
    
    return Response({
        'message': f'Driver status changed to {"active" if driver.is_active else "inactive"}',
        'driver_id': driver_id,
        'is_active': driver.is_active
    })



# Enhanced API endpoints for real-time tracking

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_active_drivers(request):
    """Get all active drivers with their current locations"""
    if request.user.user_type not in ['controller', 'admin']:
        return Response(
            {'error': 'Insufficient permissions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        drivers = Driver.objects.filter(is_active=True).select_related('user')
        drivers_data = []
        
        for driver in drivers:
            current_job = Job.objects.filter(
                driver=driver,
                status__in=['assigned', 'accepted', 'en_route']
            ).first()
            
            drivers_data.append({
                'id': driver.pk,
                'username': driver.user.username,
                'phone': driver.user.phone_number,
                'vehicle_details': driver.vehicle_details,
                'current_location': {
                    'latitude': driver.current_latitude,
                    'longitude': driver.current_longitude,
                    'last_update': driver.last_location_update.isoformat() if driver.last_location_update else None,
                    'accuracy': driver.location_accuracy
                },
                'status': {
                    'is_active': driver.is_active,
                    'is_available': driver.is_available
                },
                'current_job': {
                    'id': current_job.id,
                    'type': current_job.job_type,
                    'status': current_job.status,
                    'parcel_tracking': current_job.parcel.tracking_number,
                    'estimated_arrival': current_job.estimated_arrival_time.isoformat() if current_job.estimated_arrival_time else None
                } if current_job else None
            })
        
        return Response({
            'drivers': drivers_data,
            'total_count': len(drivers_data),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch drivers: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_driver_details(request, driver_id):
    """Get detailed information about a specific driver"""
    if request.user.user_type not in ['controller', 'admin']:
        return Response(
            {'error': 'Insufficient permissions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        driver = get_object_or_404(Driver.objects.select_related('user'), pk=driver_id)
        
        # Get recent jobs
        recent_jobs = Job.objects.filter(driver=driver).order_by('-assigned_at')[:10]
        
        # Get location history for today
        today = timezone.now().date()
        location_history = DriverLocationHistory.objects.filter(
            driver=driver,
            timestamp__date=today
        ).order_by('-timestamp')[:100]
        
        # Get current route if any
        current_route = Route.objects.filter(
            driver=driver,
            status='active'
        ).first()
        
        driver_data = {
            'id': driver.pk,
            'username': driver.user.username,
            'email': driver.user.email,
            'phone': driver.user.phone_number,
            'vehicle_details': driver.vehicle_details,
            'current_location': {
                'latitude': driver.current_latitude,
                'longitude': driver.current_longitude,
                'last_update': driver.last_location_update.isoformat() if driver.last_location_update else None,
                'accuracy': driver.location_accuracy
            },
            'status': {
                'is_active': driver.is_active,
                'is_available': driver.is_available
            },
            'performance': {
                'total_distance_today': driver.total_distance_today,
                'last_route_update': driver.last_route_update.isoformat() if driver.last_route_update else None
            },
            'recent_jobs': [
                {
                    'id': job.id,
                    'type': job.job_type,
                    'status': job.status,
                    'parcel_tracking': job.parcel.tracking_number,
                    'assigned_at': job.assigned_at.isoformat(),
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                    'estimated_arrival': job.estimated_arrival_time.isoformat() if job.estimated_arrival_time else None
                } for job in recent_jobs
            ],
            'location_history': [
                {
                    'latitude': loc.latitude,
                    'longitude': loc.longitude,
                    'timestamp': loc.timestamp.isoformat(),
                    'accuracy': loc.accuracy,
                    'speed': loc.speed,
                    'heading': loc.heading
                } for loc in location_history
            ],
            'current_route': {
                'id': current_route.id,
                'name': current_route.route_name,
                'area': current_route.route_area,
                'depot': current_route.depot,
                'status': current_route.status,
                'started_at': current_route.started_at.isoformat() if current_route.started_at else None,
                'estimated_duration': str(current_route.estimated_duration) if current_route.estimated_duration else None,
                'planned_stops': current_route.planned_stops
            } if current_route else None
        }
        
        return Response(driver_data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch driver details: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_driver_route(request, driver_id):
    """Get current route information for a driver"""
    if request.user.user_type not in ['controller', 'admin']:
        return Response(
            {'error': 'Insufficient permissions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        driver = get_object_or_404(Driver, pk=driver_id)
        
        # Get current active job
        current_job = Job.objects.filter(
            driver=driver,
            status__in=['assigned', 'accepted', 'en_route']
        ).select_related('parcel').first()
        
        if not current_job:
            return Response({
                'message': 'No active route found for this driver',
                'driver_id': driver_id
            })
        
        # Get route waypoints from location history
        location_history = DriverLocationHistory.objects.filter(
            driver=driver,
            current_job=current_job
        ).order_by('timestamp')
        
        waypoints = [
            {
                'latitude': loc.latitude,
                'longitude': loc.longitude,
                'timestamp': loc.timestamp.isoformat(),
                'speed': loc.speed,
                'heading': loc.heading
            } for loc in location_history
        ]
        
        route_data = {
            'driver_id': driver_id,
            'driver_name': driver.user.username,
            'job_id': current_job.id,
            'job_type': current_job.job_type,
            'status': current_job.status,
            'parcel': {
                'tracking_number': current_job.parcel.tracking_number,
                'pickup_address': current_job.parcel.pickup_address,
                'delivery_address': current_job.parcel.delivery_address,
                'recipient_name': current_job.parcel.recipient_name,
                'status': current_job.parcel.status
            },
            'route_details': {
                'waypoints': waypoints,
                'total_waypoints': len(waypoints),
                'estimated_arrival': current_job.estimated_arrival_time.isoformat() if current_job.estimated_arrival_time else None,
                'route_started_at': current_job.route_started_at.isoformat() if current_job.route_started_at else None,
                'estimated_distance': current_job.estimated_distance,
                'actual_distance': current_job.actual_distance
            },
            'current_location': {
                'latitude': driver.current_latitude,
                'longitude': driver.current_longitude,
                'last_update': driver.last_location_update.isoformat() if driver.last_location_update else None
            }
        }
        
        return Response(route_data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch driver route: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_driver_status(request, driver_id):
    """Update driver status (active/available)"""
    if request.user.user_type not in ['controller', 'admin']:
        return Response(
            {'error': 'Insufficient permissions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        driver = get_object_or_404(Driver, pk=driver_id)
        
        is_active = request.data.get('is_active')
        is_available = request.data.get('is_available')
        
        if is_active is not None:
            driver.is_active = is_active
        if is_available is not None:
            driver.is_available = is_available
            
        driver.save()
        
        return Response({
            'message': 'Driver status updated successfully',
            'driver_id': driver_id,
            'status': {
                'is_active': driver.is_active,
                'is_available': driver.is_available
            },
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to update driver status: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_tracking_analytics(request):
    """Get tracking analytics and statistics"""
    if request.user.user_type not in ['controller', 'admin']:
        return Response(
            {'error': 'Insufficient permissions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
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
        
        # Location updates statistics
        location_updates_today = DriverLocationHistory.objects.filter(
            timestamp__date=today
        ).count()
        
        analytics_data = {
            'timestamp': timezone.now().isoformat(),
            'date': today.isoformat(),
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
            },
            'tracking': {
                'location_updates_today': location_updates_today,
                'average_updates_per_driver': round((location_updates_today / active_drivers), 2) if active_drivers > 0 else 0
            }
        }
        
        return Response(analytics_data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch analytics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_parcel_tracking_public(request, tracking_number):
    """Public API for customer parcel tracking"""
    try:
        parcel = get_object_or_404(
            Parcel.objects.select_related('current_driver__user'),
            tracking_number=tracking_number
        )
        
        # Check if customer tracking is enabled
        if not parcel.can_customer_track:
            return Response(
                {'error': 'Tracking not available for this parcel'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get current job
        current_job = Job.objects.filter(
            parcel=parcel,
            status__in=['assigned', 'accepted', 'en_route']
        ).select_related('driver__user').first()
        
        # Get tracking events
        tracking_events = parcel.tracking_events.all()[:10]
        
        driver_location = None
        if current_job and current_job.driver and current_job.customer_tracking_enabled:
            driver = current_job.driver
            if driver.current_latitude and driver.current_longitude:
                driver_location = {
                    'latitude': driver.current_latitude,
                    'longitude': driver.current_longitude,
                    'last_update': driver.last_location_update.isoformat() if driver.last_location_update else None,
                    'accuracy': driver.location_accuracy
                }
        
        parcel_data = {
            'tracking_number': parcel.tracking_number,
            'status': parcel.status,
            'pickup_address': parcel.pickup_address,
            'delivery_address': parcel.delivery_address,
            'recipient_name': parcel.recipient_name,
            'expected_delivery': parcel.expected_delivery_date.isoformat() if parcel.expected_delivery_date else None,
            'current_driver': {
                'name': current_job.driver.user.username,
                'phone': current_job.driver.user.phone_number,
                'location': driver_location
            } if current_job and current_job.driver else None,
            'tracking_events': [
                {
                    'timestamp': event.timestamp.isoformat(),
                    'location': event.location,
                    'status_update': event.status_update,
                    'notes': event.notes
                } for event in tracking_events
            ],
            'last_updated': timezone.now().isoformat()
        }
        
        return Response(parcel_data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch parcel tracking: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

