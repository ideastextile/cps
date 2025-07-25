import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Driver, Parcel, DriverLocationHistory, Job
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class DriverTrackingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for driver location updates"""
    
    async def connect(self):
        self.driver_id = self.scope['url_route']['kwargs']['driver_id']
        self.room_group_name = f'driver_tracking_{self.driver_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Driver {self.driver_id} connected to tracking")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Driver {self.driver_id} disconnected from tracking")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'location_update':
                await self.handle_location_update(text_data_json)
            elif message_type == 'status_update':
                await self.handle_status_update(text_data_json)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in driver tracking consumer: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': 'Internal server error'
            }))

    async def handle_location_update(self, data):
        """Handle driver location updates"""
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy')
        speed = data.get('speed')
        heading = data.get('heading')
        
        if latitude is None or longitude is None:
            await self.send(text_data=json.dumps({
                'error': 'Latitude and longitude are required'
            }))
            return
            
        # Update driver location in database
        await self.update_driver_location(
            self.driver_id, latitude, longitude, accuracy, speed, heading
        )
        
        # Broadcast to admin dashboard
        await self.channel_layer.group_send(
            'admin_tracking',
            {
                'type': 'driver_location_update',
                'driver_id': self.driver_id,
                'latitude': latitude,
                'longitude': longitude,
                'accuracy': accuracy,
                'speed': speed,
                'heading': heading,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Send confirmation back to driver
        await self.send(text_data=json.dumps({
            'type': 'location_update_confirmed',
            'timestamp': timezone.now().isoformat()
        }))

    async def handle_status_update(self, data):
        """Handle driver status updates"""
        is_active = data.get('is_active')
        is_available = data.get('is_available')
        
        await self.update_driver_status(self.driver_id, is_active, is_available)
        
        # Broadcast to admin dashboard
        await self.channel_layer.group_send(
            'admin_tracking',
            {
                'type': 'driver_status_update',
                'driver_id': self.driver_id,
                'is_active': is_active,
                'is_available': is_available,
                'timestamp': timezone.now().isoformat()
            }
        )

    @database_sync_to_async
    def update_driver_location(self, driver_id, latitude, longitude, accuracy=None, speed=None, heading=None):
        """Update driver location in database"""
        try:
            driver = Driver.objects.get(pk=driver_id)
            
            # Update current location
            driver.current_latitude = latitude
            driver.current_longitude = longitude
            driver.last_location_update = timezone.now()
            driver.location_accuracy = accuracy
            driver.save()
            
            # Get current job if any
            current_job = Job.objects.filter(
                driver=driver,
                status__in=['assigned', 'accepted', 'en_route']
            ).first()
            
            # Save location history
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
        except Driver.DoesNotExist:
            logger.error(f"Driver {driver_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error updating driver location: {str(e)}")
            return False

    @database_sync_to_async
    def update_driver_status(self, driver_id, is_active=None, is_available=None):
        """Update driver status in database"""
        try:
            driver = Driver.objects.get(pk=driver_id)
            
            if is_active is not None:
                driver.is_active = is_active
            if is_available is not None:
                driver.is_available = is_available
                
            driver.save()
            return True
        except Driver.DoesNotExist:
            logger.error(f"Driver {driver_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error updating driver status: {str(e)}")
            return False


class AdminTrackingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for admin dashboard real-time updates"""
    
    async def connect(self):
        self.room_group_name = 'admin_tracking'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        await self.send_initial_data()
        logger.info("Admin connected to tracking dashboard")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info("Admin disconnected from tracking dashboard")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'get_driver_details':
                driver_id = text_data_json.get('driver_id')
                await self.send_driver_details(driver_id)
            elif message_type == 'get_driver_route':
                driver_id = text_data_json.get('driver_id')
                await self.send_driver_route(driver_id)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))

    async def send_initial_data(self):
        """Send initial driver data to admin dashboard"""
        drivers_data = await self.get_all_active_drivers()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'drivers': drivers_data
        }))

    async def send_driver_details(self, driver_id):
        """Send detailed driver information"""
        driver_details = await self.get_driver_details(driver_id)
        await self.send(text_data=json.dumps({
            'type': 'driver_details',
            'driver': driver_details
        }))

    async def send_driver_route(self, driver_id):
        """Send driver route information"""
        route_data = await self.get_driver_route(driver_id)
        await self.send(text_data=json.dumps({
            'type': 'driver_route',
            'driver_id': driver_id,
            'route': route_data
        }))

    # Receive message from room group
    async def driver_location_update(self, event):
        """Handle driver location updates from room group"""
        await self.send(text_data=json.dumps({
            'type': 'driver_location_update',
            'driver_id': event['driver_id'],
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'accuracy': event.get('accuracy'),
            'speed': event.get('speed'),
            'heading': event.get('heading'),
            'timestamp': event['timestamp']
        }))

    async def driver_status_update(self, event):
        """Handle driver status updates from room group"""
        await self.send(text_data=json.dumps({
            'type': 'driver_status_update',
            'driver_id': event['driver_id'],
            'is_active': event['is_active'],
            'is_available': event['is_available'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def get_all_active_drivers(self):
        """Get all active drivers with their current locations"""
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
                    'latitude': driver.current_latitude,
                    'longitude': driver.current_longitude,
                    'last_update': driver.last_location_update.isoformat() if driver.last_location_update else None,
                    'is_available': driver.is_available,
                    'is_active': driver.is_active,
                    'current_job': {
                        'id': current_job.id,
                        'type': current_job.job_type,
                        'status': current_job.status,
                        'parcel_tracking': current_job.parcel.tracking_number
                    } if current_job else None
                })
            
            return drivers_data
        except Exception as e:
            logger.error(f"Error getting active drivers: {str(e)}")
            return []

    @database_sync_to_async
    def get_driver_details(self, driver_id):
        """Get detailed driver information"""
        try:
            driver = Driver.objects.select_related('user').get(pk=driver_id)
            
            # Get recent jobs
            recent_jobs = Job.objects.filter(driver=driver).order_by('-assigned_at')[:5]
            
            # Get location history for today
            today = timezone.now().date()
            location_history = DriverLocationHistory.objects.filter(
                driver=driver,
                timestamp__date=today
            ).order_by('-timestamp')[:50]
            
            return {
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
                'recent_jobs': [
                    {
                        'id': job.id,
                        'type': job.job_type,
                        'status': job.status,
                        'parcel_tracking': job.parcel.tracking_number,
                        'assigned_at': job.assigned_at.isoformat()
                    } for job in recent_jobs
                ],
                'location_history': [
                    {
                        'latitude': loc.latitude,
                        'longitude': loc.longitude,
                        'timestamp': loc.timestamp.isoformat(),
                        'speed': loc.speed,
                        'heading': loc.heading
                    } for loc in location_history
                ]
            }
        except Driver.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting driver details: {str(e)}")
            return None

    @database_sync_to_async
    def get_driver_route(self, driver_id):
        """Get driver route information"""
        try:
            driver = Driver.objects.get(pk=driver_id)
            
            # Get current active job
            current_job = Job.objects.filter(
                driver=driver,
                status__in=['assigned', 'accepted', 'en_route']
            ).select_related('parcel').first()
            
            if not current_job:
                return None
                
            # Get route waypoints from location history
            location_history = DriverLocationHistory.objects.filter(
                driver=driver,
                current_job=current_job
            ).order_by('timestamp')
            
            waypoints = [
                {
                    'latitude': loc.latitude,
                    'longitude': loc.longitude,
                    'timestamp': loc.timestamp.isoformat()
                } for loc in location_history
            ]
            
            return {
                'job_id': current_job.id,
                'job_type': current_job.job_type,
                'status': current_job.status,
                'parcel': {
                    'tracking_number': current_job.parcel.tracking_number,
                    'pickup_address': current_job.parcel.pickup_address,
                    'delivery_address': current_job.parcel.delivery_address
                },
                'waypoints': waypoints,
                'estimated_arrival': current_job.estimated_arrival_time.isoformat() if current_job.estimated_arrival_time else None
            }
        except Driver.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting driver route: {str(e)}")
            return None


class ParcelTrackingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for customer parcel tracking"""
    
    async def connect(self):
        self.tracking_number = self.scope['url_route']['kwargs']['tracking_number']
        self.room_group_name = f'parcel_tracking_{self.tracking_number}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial parcel data
        await self.send_parcel_data()
        logger.info(f"Customer connected to parcel tracking: {self.tracking_number}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Customer disconnected from parcel tracking: {self.tracking_number}")

    async def send_parcel_data(self):
        """Send current parcel tracking data"""
        parcel_data = await self.get_parcel_data(self.tracking_number)
        if parcel_data:
            await self.send(text_data=json.dumps({
                'type': 'parcel_data',
                'parcel': parcel_data
            }))

    @database_sync_to_async
    def get_parcel_data(self, tracking_number):
        """Get parcel tracking data"""
        try:
            parcel = Parcel.objects.select_related('current_driver__user').get(
                tracking_number=tracking_number
            )
            
            # Get current job
            current_job = Job.objects.filter(
                parcel=parcel,
                status__in=['assigned', 'accepted', 'en_route']
            ).select_related('driver__user').first()
            
            # Get tracking events
            tracking_events = parcel.tracking_events.all()[:10]
            
            driver_location = None
            if current_job and current_job.driver:
                driver = current_job.driver
                if driver.current_latitude and driver.current_longitude:
                    driver_location = {
                        'latitude': driver.current_latitude,
                        'longitude': driver.current_longitude,
                        'last_update': driver.last_location_update.isoformat() if driver.last_location_update else None
                    }
            
            return {
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
                ]
            }
        except Parcel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting parcel data: {str(e)}")
            return None

    # Receive message from room group
    async def parcel_update(self, event):
        """Handle parcel updates from room group"""
        await self.send(text_data=json.dumps({
            'type': 'parcel_update',
            'tracking_number': event['tracking_number'],
            'status': event['status'],
            'location': event.get('location'),
            'timestamp': event['timestamp']
        }))

