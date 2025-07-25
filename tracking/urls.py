from django.urls import path
from . import views
from .views import UpdateLocationView, update_job_inline
from .api_views import (
    DriverLocationUpdateAPIView, AdminDriverLocationsAPIView, DriverRouteHistoryAPIView,
    CustomerTrackingAPIView, EnableCustomerTrackingAPIView, DriverLocationWebhookAPIView,
    RouteOptimizationAPIView, get_driver_status, toggle_driver_active_status,
    get_active_drivers, get_driver_details, get_driver_route, update_driver_status,
    get_tracking_analytics, get_parcel_tracking_public
)


urlpatterns = [
    # Authentication
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),

    # Customer endpoints
    path('parcels/book/', views.ParcelBookingView.as_view(), name='book_parcel'),
    path('parcels/my_parcels/', views.CustomerParcelsView.as_view(), name='customer_parcels'),
    path('parcels/<str:tracking_number>/', views.ParcelDetailView.as_view(), name='parcel_detail'),

    # Public tracking
    path('public/track/<str:tracking_number>/', views.PublicTrackingView.as_view(), name='public_tracking'),

    # Controller endpoints
    path('parcels/', views.AllParcelsView.as_view(), name='all_parcels'),
    path('drivers/', views.AllDriversView.as_view(), name='all_drivers'),
    path('parcels/<int:parcel_id>/assign_driver/', views.AssignDriverView.as_view(), name='assign_driver'),

    # Driver endpoints
    path('jobs/my_jobs/', views.DriverJobsView.as_view(), name='driver_jobs'),
    path('jobs/<int:job_id>/accept/', views.AcceptJobView.as_view(), name='accept_job'),
    path('jobs/<int:job_id>/scan_parcel/', views.ScanParcelView.as_view(), name='scan_parcel'),
    path('jobs/<int:job_id>/complete_delivery/', views.CompleteDeliveryView.as_view(), name='complete_delivery'),
    path('driver/update_location/', views.UpdateLocationView.as_view(), name='update_location'),

    # Real-time tracking API endpoints
    path('api/driver/location/update/', DriverLocationUpdateAPIView.as_view(), name='api_driver_location_update'),
    path('api/driver/location/webhook/', DriverLocationWebhookAPIView.as_view(), name='api_driver_location_webhook'),
    path('api/admin/drivers/locations/', AdminDriverLocationsAPIView.as_view(), name='api_admin_driver_locations'),
    path('api/driver/<int:driver_id>/route-history/', DriverRouteHistoryAPIView.as_view(), name='api_driver_route_history'),
    path('api/driver/<int:driver_id>/status/', get_driver_status, name='api_driver_status'),
    path('api/driver/<int:driver_id>/toggle-active/', toggle_driver_active_status, name='api_toggle_driver_active'),
    path('api/customer/track/<str:tracking_number>/location/', CustomerTrackingAPIView.as_view(), name='api_customer_tracking'),
    path('api/admin/job/<int:job_id>/enable-tracking/', EnableCustomerTrackingAPIView.as_view(), name='api_enable_customer_tracking'),
    path('api/route/optimize/', RouteOptimizationAPIView.as_view(), name='api_route_optimization'),
    
    # New enhanced real-time tracking endpoints
    path('api/admin/drivers/active/', get_active_drivers, name='api_get_active_drivers'),
    path('api/admin/driver/<int:driver_id>/details/', get_driver_details, name='api_get_driver_details'),
    path('api/admin/driver/<int:driver_id>/route/', get_driver_route, name='api_get_driver_route'),
    path('api/admin/driver/<int:driver_id>/status/update/', update_driver_status, name='api_update_driver_status'),
    path('api/admin/analytics/', get_tracking_analytics, name='api_get_tracking_analytics'),
    path('api/public/track/<str:tracking_number>/', get_parcel_tracking_public, name='api_get_parcel_tracking_public'),
    
    # Driver simulator for testing
    path('simulator/', views.DriverSimulatorView.as_view(), name='driver_simulator'),

    # Notifications
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
    path('notifications/<int:notification_id>/mark_read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),

    # Web interface URLs
    path('', views.home1_view, name='home1'),
    path('home/', views.home_view, name='home'),
    path('about-us/',views.about_view, name='about-us'),
    path('services/',views.services_page, name='services'),
    path('contact/', views.contact_view, name='contact'),
    path("generate-label/",views.generate_label, name="generate_label"),
    path('login/', views.login_page, name='login_page'),
    path('register/', views.register_page, name='register_page'),
    path('logout/', views.logout_page, name='logout_page'),
    path('track/', views.track_parcel_page, name='track_parcel'),
    path('book-parcel/', views.book_parcel_page, name='book_parcel_page'),
    path('my-parcels/', views.my_parcels_page, name='my_parcels'),
    path('admin-dashboard/', views.admin_dashboard_page, name='admin_dashboard'),
    path('admin-dashboard/parcel/<int:parcel_id>/edit/', views.update_parcel_admin, name='update_parcel_admin'),
    path('admin-dashboard/parcel/<int:parcel_id>/delete/', views.delete_parcel_admin, name='delete_parcel_admin'),
    path('admin-dashboard/', views.admin_dashboard_page, name='admin_dashboard_page'),
    path('driver-dashboard/', views.driver_dashboard_page, name='driver_dashboard'),
    path('profile/', views.profile_page, name='profile'),
    path('jobs/update-inline/<int:job_id>/', update_job_inline, name='update_job_inline'),
    path('api/driver/update-location/', UpdateLocationView.as_view(), name='update_location'),
    path('book-parcel/', views.book_parcel_page, name='book_parcel_page'),
    path('label/<int:parcel_id>/', views.print_label, name='print_label'),


    # Enhanced parcel tracking and delivery management
    path('enhanced-tracking/', views.enhanced_parcel_tracking, name='enhanced_parcel_tracking'),
    path('delivery-management/', views.delivery_management_dashboard, name='delivery_management_dashboard'),
    
    # Enhanced delivery API endpoints
    path('api/job/<int:job_id>/start-route/', views.start_job_route, name='api_start_job_route'),
    path('api/job/<int:job_id>/complete-enhanced/', views.complete_delivery_enhanced, name='api_complete_delivery_enhanced'),
    path('api/job/<int:job_id>/report-issue/', views.report_delivery_issue, name='api_report_delivery_issue'),
    path('api/driver/performance/', views.get_driver_performance, name='api_get_driver_performance'),
    path('api/job/<int:job_id>/enable-tracking-enhanced/', views.enable_customer_tracking_enhanced, name='api_enable_customer_tracking_enhanced'),
    
    # Live tracking and enhanced admin interfaces
    path('live-tracking/', views.live_tracking_dashboard, name='live_tracking_dashboard'),
    path('enhanced-admin/', views.enhanced_admin_dashboard, name='enhanced_admin_dashboard'),
    path('driver-management/', views.driver_management, name='driver_management'),
    path('route-management/', views.route_management, name='route_management'),
    path('parcel-tracking-management/', views.parcel_tracking_management, name='parcel_tracking_management'),
    path('tracking-analytics/', views.tracking_analytics, name='tracking_analytics'),
    
    #website urls
    

]

