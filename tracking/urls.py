from django.urls import path
from . import views
from .views import UpdateLocationView, update_job_inline


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


    #website urls
    

]

