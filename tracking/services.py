"""
Google Maps integration services for the courier tracking system
"""
import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import json
import logging

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Service class for Google Maps API integration"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
        self.base_url = 'https://maps.googleapis.com/maps/api'
    
    def geocode_address(self, address):
        """
        Convert address to coordinates using Google Geocoding API
        
        Args:
            address (str): Address to geocode
            
        Returns:
            dict: {'lat': float, 'lng': float} or None if failed
        """
        if not self.api_key or self.api_key == 'YOUR_GOOGLE_MAPS_API_KEY_HERE':
            # Fallback to mock coordinates for demo purposes
            return self._get_mock_coordinates(address)
        
        url = f"{self.base_url}/geocode/json"
        params = {
            'address': address,
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return {'lat': location['lat'], 'lng': location['lng']}
            else:
                logger.warning(f"Geocoding failed for address: {address}, Status: {data['status']}")
                return self._get_mock_coordinates(address)
                
        except Exception as e:
            logger.error(f"Error geocoding address {address}: {str(e)}")
            return self._get_mock_coordinates(address)
    
    def _get_mock_coordinates(self, address):
        """
        Generate mock coordinates for demo purposes
        
        Args:
            address (str): Address to generate mock coordinates for
            
        Returns:
            dict: Mock coordinates based on address hash
        """
        # Generate consistent mock coordinates based on address
        import hashlib
        hash_obj = hashlib.md5(address.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert hash to coordinates within UK bounds
        lat_offset = int(hash_hex[:4], 16) % 1000 / 10000  # 0-0.1 degree variation
        lng_offset = int(hash_hex[4:8], 16) % 1000 / 10000
        
        # Base coordinates for UK (London area)
        base_lat = 51.5074 + lat_offset
        base_lng = -0.1278 + lng_offset
        
        return {'lat': base_lat, 'lng': base_lng}
    
    def calculate_route(self, origin, destination, waypoints=None):
        """
        Calculate route between origin and destination with optional waypoints
        
        Args:
            origin (dict): {'lat': float, 'lng': float}
            destination (dict): {'lat': float, 'lng': float}
            waypoints (list): List of waypoint coordinates
            
        Returns:
            dict: Route information including distance, duration, and polyline
        """
        if not self.api_key or self.api_key == 'YOUR_GOOGLE_MAPS_API_KEY_HERE':
            return self._get_mock_route(origin, destination, waypoints)
        
        url = f"{self.base_url}/directions/json"
        params = {
            'origin': f"{origin['lat']},{origin['lng']}",
            'destination': f"{destination['lat']},{destination['lng']}",
            'key': self.api_key,
            'mode': 'driving'
        }
        
        if waypoints:
            waypoint_str = '|'.join([f"{wp['lat']},{wp['lng']}" for wp in waypoints])
            params['waypoints'] = waypoint_str
            params['optimize_waypoints'] = 'true'
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK' and data['routes']:
                route = data['routes'][0]
                leg = route['legs'][0]
                
                return {
                    'distance_km': leg['distance']['value'] / 1000,
                    'duration_minutes': leg['duration']['value'] / 60,
                    'polyline': route['overview_polyline']['points'],
                    'waypoint_order': data.get('waypoint_order', []),
                    'steps': [step['html_instructions'] for step in leg['steps']]
                }
            else:
                logger.warning(f"Route calculation failed: {data['status']}")
                return self._get_mock_route(origin, destination, waypoints)
                
        except Exception as e:
            logger.error(f"Error calculating route: {str(e)}")
            return self._get_mock_route(origin, destination, waypoints)
    
    def _get_mock_route(self, origin, destination, waypoints=None):
        """Generate mock route data for demo purposes"""
        # Calculate approximate distance using Haversine formula
        import math
        
        def haversine_distance(lat1, lng1, lat2, lng2):
            R = 6371  # Earth's radius in kilometers
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = (math.sin(dlat/2) * math.sin(dlat/2) + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dlng/2) * math.sin(dlng/2))
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        distance = haversine_distance(
            origin['lat'], origin['lng'],
            destination['lat'], destination['lng']
        )
        
        # Estimate duration (assuming average speed of 40 km/h in city)
        duration = distance / 40 * 60  # minutes
        
        return {
            'distance_km': round(distance, 2),
            'duration_minutes': round(duration, 1),
            'polyline': 'mock_polyline_data',
            'waypoint_order': list(range(len(waypoints))) if waypoints else [],
            'steps': ['Mock driving directions']
        }
    
    def calculate_eta(self, current_location, destination):
        """
        Calculate estimated time of arrival
        
        Args:
            current_location (dict): Current coordinates
            destination (dict): Destination coordinates
            
        Returns:
            datetime: Estimated arrival time
        """
        route_info = self.calculate_route(current_location, destination)
        duration_minutes = route_info.get('duration_minutes', 30)  # Default 30 minutes
        
        return timezone.now() + timedelta(minutes=duration_minutes)
    
    def optimize_route(self, start_location, stops, end_location=None):
        """
        Optimize delivery route using Google Maps Directions API
        
        Args:
            start_location (dict): Starting coordinates
            stops (list): List of stop coordinates
            end_location (dict): Ending coordinates (optional)
            
        Returns:
            dict: Optimized route information
        """
        if not end_location:
            end_location = start_location
        
        route_info = self.calculate_route(start_location, end_location, stops)
        
        return {
            'optimized_order': route_info.get('waypoint_order', []),
            'total_distance_km': route_info.get('distance_km', 0),
            'estimated_duration_minutes': route_info.get('duration_minutes', 0),
            'route_polyline': route_info.get('polyline', ''),
            'driving_steps': route_info.get('steps', [])
        }


class LocationTrackingService:
    """Service for managing driver location tracking"""
    
    @staticmethod
    def update_driver_location(driver, latitude, longitude, accuracy=None, speed=None, heading=None):
        """
        Update driver's current location and store in history
        
        Args:
            driver: Driver instance
            latitude (float): GPS latitude
            longitude (float): GPS longitude
            accuracy (float): GPS accuracy in meters
            speed (float): Speed in km/h
            heading (float): Direction in degrees
            
        Returns:
            bool: Success status
        """
        from .models import DriverLocationHistory
        from django.utils import timezone
        
        try:
            # Update driver's current location
            driver.current_latitude = latitude
            driver.current_longitude = longitude
            driver.last_location_update = timezone.now()
            if accuracy is not None:
                driver.location_accuracy = accuracy
            driver.save()
            
            # Store in location history
            current_job = driver.jobs.filter(status__in=['accepted', 'en_route']).first()
            
            DriverLocationHistory.objects.create(
                driver=driver,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                speed=speed,
                heading=heading,
                current_job=current_job
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating driver location: {str(e)}")
            return False
    
    @staticmethod
    def get_driver_route_history(driver, hours=24):
        """
        Get driver's location history for route visualization
        
        Args:
            driver: Driver instance
            hours (int): Number of hours to look back
            
        Returns:
            list: List of location points
        """
        from .models import DriverLocationHistory
        from django.utils import timezone
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        locations = DriverLocationHistory.objects.filter(
            driver=driver,
            timestamp__gte=cutoff_time
        ).order_by('timestamp').values(
            'latitude', 'longitude', 'timestamp', 'speed', 'heading'
        )
        
        return list(locations)
    
    @staticmethod
    def get_active_drivers_locations():
        """
        Get current locations of all active drivers
        
        Returns:
            list: List of driver location data
        """
        from .models import Driver
        
        active_drivers = Driver.objects.filter(
            is_active=True,
            current_latitude__isnull=False,
            current_longitude__isnull=False
        ).select_related('user').prefetch_related('jobs')
        
        driver_locations = []
        for driver in active_drivers:
            current_job = driver.jobs.filter(status__in=['accepted', 'en_route']).first()
            
            driver_locations.append({
                'driver_id': driver.pk,
                'username': driver.user.username,
                'latitude': driver.current_latitude,
                'longitude': driver.current_longitude,
                'last_update': driver.last_location_update,
                'accuracy': driver.location_accuracy,
                'is_available': driver.is_available,
                'current_job': {
                    'id': current_job.id,
                    'parcel_tracking': current_job.parcel.tracking_number,
                    'job_type': current_job.job_type,
                    'status': current_job.status
                } if current_job else None
            })
        
        return driver_locations

