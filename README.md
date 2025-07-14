# ParcelTrack Pro - Complete Parcel Tracking System

A comprehensive parcel tracking and delivery management system built with Django backend, responsive web interface, and mobile app integration.

## 🚀 Features

### Customer Features
- **Parcel Booking**: Schedule parcel pickups with detailed information
- **Real-time Tracking**: Track parcels with live updates and notifications
- **Account Management**: User registration, login, and profile management
- **Parcel History**: View all past and current parcels in one dashboard

### Driver Features
- **Job Management**: Receive and manage pickup/delivery jobs
- **Parcel Scanning**: Scan parcels with QR/barcode functionality
- **Location Updates**: Real-time location tracking
- **Photo Proof**: Capture delivery photos and signatures
- **Mobile-Optimized Interface**: Responsive design for mobile devices

### Controller/Admin Features
- **Dispatch Management**: Assign jobs to drivers
- **Parcel Monitoring**: Track all parcels in the system
- **Driver Management**: Manage driver accounts and availability
- **Analytics Dashboard**: View system statistics and performance

### System Features
- **Real-time Notifications**: Browser and in-app notifications
- **RESTful API**: Complete API for mobile app integration
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Secure Authentication**: Role-based access control
- **Tracking History**: Complete audit trail for all parcels

## 🛠️ Technology Stack

- **Backend**: Django 5.2.4 with Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: Django's built-in authentication system
- **Real-time Updates**: JavaScript polling with notification API
- **Deployment**: Ready for cloud deployment

## 📋 System Requirements

- Python 3.11+
- Django 5.2.4
- Django REST Framework
- Django CORS Headers
- Pillow (for image handling)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
cd parcel_tracking_system

# Install dependencies
pip install django djangorestframework django-cors-headers pillow

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Create test data
python create_test_data.py

# Start development server
python manage.py runserver 0.0.0.0:8000
```

### 2. Access the System

- **Website**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api

### 3. Test Accounts

The system comes with pre-created test accounts:

| Role | Username | Password | Description |
|------|----------|----------|-------------|
| Customer | customer1 | password123 | John Doe - Has 2 parcels |
| Customer | customer2 | password123 | Jane Smith - Has 1 parcel |
| Driver | driver1 | password123 | Bob Wilson - Available driver |
| Driver | driver2 | password123 | Alice Brown - Available driver |
| Controller | controller1 | password123 | Mike Johnson - System admin |
| Admin | admin | admin123 | System administrator |

## 📱 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/register/` - User registration

### Parcels
- `GET /api/parcels/` - List user's parcels
- `POST /api/parcels/` - Create new parcel
- `GET /api/parcels/{id}/` - Get parcel details
- `PUT /api/parcels/{id}/` - Update parcel
- `GET /api/public/track/{tracking_number}/` - Public tracking

### Jobs (Driver)
- `GET /api/jobs/` - List driver's jobs
- `POST /api/jobs/{id}/accept/` - Accept job
- `POST /api/jobs/{id}/scan_parcel/` - Scan parcel
- `POST /api/jobs/{id}/complete_delivery/` - Complete delivery

### Tracking
- `GET /api/tracking_events/` - List tracking events
- `POST /api/tracking_events/` - Create tracking event

### Notifications
- `GET /api/notifications/` - List user notifications
- `POST /api/notifications/{id}/mark_read/` - Mark as read

## 🎯 User Workflows

### Customer Workflow
1. **Register/Login** → Access customer dashboard
2. **Book Parcel** → Fill pickup and delivery details
3. **Track Parcel** → Monitor real-time status updates
4. **Receive Notifications** → Get updates on parcel status

### Driver Workflow
1. **Login** → Access driver dashboard
2. **View Jobs** → See assigned pickup/delivery jobs
3. **Accept Job** → Confirm job acceptance
4. **Scan Parcel** → Scan QR code when collecting
5. **Update Location** → Real-time location tracking
6. **Complete Delivery** → Upload photo and get signature

### Controller Workflow
1. **Login** → Access admin dashboard
2. **Monitor Parcels** → View all system parcels
3. **Assign Jobs** → Dispatch jobs to available drivers
4. **Manage System** → Oversee operations and analytics

## 🔧 Configuration

### Environment Variables
```bash
# Django settings
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (for production)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Email settings (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### CORS Settings
The system is configured to allow cross-origin requests for API access:
```python
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
```

## 📊 Database Schema

### Core Models
- **User**: Extended Django user with role-based access
- **Driver**: Driver profile with vehicle and location info
- **Parcel**: Main parcel entity with tracking information
- **TrackingEvent**: Audit trail of parcel status changes
- **Job**: Driver job assignments for pickup/delivery
- **Notification**: User notifications system

### Key Relationships
- User → Parcel (one-to-many)
- Driver → Job (one-to-many)
- Parcel → TrackingEvent (one-to-many)
- Parcel → Job (one-to-many)

## 🔒 Security Features

- **Authentication**: Session-based authentication
- **Authorization**: Role-based access control
- **CSRF Protection**: Built-in Django CSRF protection
- **Input Validation**: Form and API input validation
- **SQL Injection Protection**: Django ORM protection
- **XSS Protection**: Template auto-escaping

## 📱 Mobile App Integration

The system provides a complete REST API for mobile app development:

### Key API Features
- Token-based authentication
- Real-time job updates
- Image upload for delivery proof
- Location tracking endpoints
- Push notification support (ready for implementation)

### Mobile App Workflow
1. **Authentication** → Login with username/password
2. **Job Sync** → Fetch assigned jobs
3. **Offline Support** → Cache data for offline access
4. **Real-time Updates** → Polling or WebSocket integration
5. **Media Upload** → Photos and signatures

## 🚀 Deployment

### Development Deployment
```bash
python manage.py runserver 0.0.0.0:8000
```

### Production Deployment
1. **Configure Environment Variables**
2. **Set up Database** (PostgreSQL recommended)
3. **Configure Static Files** (`collectstatic`)
4. **Set up Web Server** (Nginx + Gunicorn)
5. **Configure SSL** (Let's Encrypt)

### Docker Deployment (Optional)
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 📈 Performance Optimization

- **Database Indexing**: Optimized queries with proper indexes
- **Caching**: Ready for Redis/Memcached integration
- **Static Files**: CDN-ready static file serving
- **API Pagination**: Efficient data loading
- **Image Optimization**: Automatic image resizing

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Test Coverage
- Model validation tests
- API endpoint tests
- Authentication tests
- Business logic tests

## 📞 Support & Documentation

### API Documentation
- Swagger/OpenAPI documentation available
- Postman collection for API testing
- Example requests and responses

### Troubleshooting
- Check Django logs for errors
- Verify database connections
- Ensure proper CORS configuration
- Validate API authentication

## 🔄 Future Enhancements

- **WebSocket Integration**: Real-time updates
- **Push Notifications**: Mobile push notifications
- **Advanced Analytics**: Detailed reporting dashboard
- **Multi-language Support**: Internationalization
- **Payment Integration**: Online payment processing
- **GPS Tracking**: Real-time driver location
- **Route Optimization**: Efficient delivery routes

## 📄 License

This project is proprietary software developed for parcel tracking and delivery management.

## 👥 Contributors

Developed by the Manus AI team for comprehensive parcel tracking solutions.

---

**ParcelTrack Pro** - Professional parcel tracking and delivery management system.

