from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/tracking/driver/(?P<driver_id>\w+)/$', consumers.DriverTrackingConsumer.as_asgi()),
    re_path(r'ws/tracking/admin/$', consumers.AdminTrackingConsumer.as_asgi()),
    re_path(r'ws/tracking/parcel/(?P<tracking_number>\w+)/$', consumers.ParcelTrackingConsumer.as_asgi()),
]

