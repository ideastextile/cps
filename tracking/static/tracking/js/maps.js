/**
 * Google Maps integration for real-time driver tracking
 * Supports both admin dashboard and customer tracking interfaces
 */

class DriverTrackingMap {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.options = {
            zoom: 10,
            center: { lat: 51.5074, lng: -0.1278 }, // Default to London
            mapTypeId: 'roadmap',
            ...options
        };
        
        this.map = null;
        this.driverMarkers = new Map();
        this.routePolylines = new Map();
        this.infoWindows = new Map();
        this.updateInterval = null;
        this.isInitialized = false;
        
        // Initialize map when Google Maps API is loaded
        this.initializeMap();
    }
    
    initializeMap() {
        if (typeof google === 'undefined' || !google.maps) {
            console.error('Google Maps API not loaded');
            return;
        }
        
        const mapContainer = document.getElementById(this.containerId);
        if (!mapContainer) {
            console.error(`Map container with ID '${this.containerId}' not found`);
            return;
        }
        
        this.map = new google.maps.Map(mapContainer, this.options);
        this.isInitialized = true;
        
        console.log('Google Maps initialized successfully');
    }
    
    /**
     * Add or update driver marker on the map
     */
    updateDriverLocation(driverId, location, info = {}) {
        if (!this.isInitialized) {
            console.warn('Map not initialized yet');
            return;
        }
        
        const position = { lat: location.latitude, lng: location.longitude };
        
        if (this.driverMarkers.has(driverId)) {
            // Update existing marker
            const marker = this.driverMarkers.get(driverId);
            marker.setPosition(position);
            
            // Update info window content
            if (this.infoWindows.has(driverId)) {
                const infoWindow = this.infoWindows.get(driverId);
                infoWindow.setContent(this.createInfoWindowContent(info));
            }
        } else {
            // Create new marker
            const marker = new google.maps.Marker({
                position: position,
                map: this.map,
                title: info.driverName || `Driver ${driverId}`,
                icon: this.getDriverIcon(info.status || 'available'),
                animation: google.maps.Animation.DROP
            });
            
            // Create info window
            const infoWindow = new google.maps.InfoWindow({
                content: this.createInfoWindowContent(info)
            });
            
            // Add click listener to show info window
            marker.addListener('click', () => {
                // Close all other info windows
                this.infoWindows.forEach(iw => iw.close());
                infoWindow.open(this.map, marker);
            });
            
            this.driverMarkers.set(driverId, marker);
            this.infoWindows.set(driverId, infoWindow);
        }
        
        // Update last seen time
        if (info.lastUpdate) {
            const marker = this.driverMarkers.get(driverId);
            marker.lastUpdate = new Date(info.lastUpdate);
        }
    }
    
    /**
     * Remove driver marker from the map
     */
    removeDriverMarker(driverId) {
        if (this.driverMarkers.has(driverId)) {
            const marker = this.driverMarkers.get(driverId);
            marker.setMap(null);
            this.driverMarkers.delete(driverId);
        }
        
        if (this.infoWindows.has(driverId)) {
            const infoWindow = this.infoWindows.get(driverId);
            infoWindow.close();
            this.infoWindows.delete(driverId);
        }
    }
    
    /**
     * Display driver route on the map
     */
    showDriverRoute(driverId, routePoints, options = {}) {
        if (!this.isInitialized) return;
        
        // Remove existing route
        if (this.routePolylines.has(driverId)) {
            this.routePolylines.get(driverId).setMap(null);
        }
        
        const routePath = new google.maps.Polyline({
            path: routePoints.map(point => ({ lat: point.latitude, lng: point.longitude })),
            geodesic: true,
            strokeColor: options.color || '#FF0000',
            strokeOpacity: options.opacity || 1.0,
            strokeWeight: options.weight || 3
        });
        
        routePath.setMap(this.map);
        this.routePolylines.set(driverId, routePath);
    }
    
    /**
     * Hide driver route
     */
    hideDriverRoute(driverId) {
        if (this.routePolylines.has(driverId)) {
            this.routePolylines.get(driverId).setMap(null);
            this.routePolylines.delete(driverId);
        }
    }
    
    /**
     * Get appropriate icon for driver status
     */
    getDriverIcon(status) {
        const iconBase = '/static/tracking/img/';
        const icons = {
            'available': {
                url: iconBase + 'driver-available.png',
                scaledSize: new google.maps.Size(32, 32)
            },
            'busy': {
                url: iconBase + 'driver-busy.png',
                scaledSize: new google.maps.Size(32, 32)
            },
            'offline': {
                url: iconBase + 'driver-offline.png',
                scaledSize: new google.maps.Size(32, 32)
            }
        };
        
        // Fallback to default marker if custom icons not available
        return icons[status] || {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 8,
            fillColor: status === 'available' ? '#00FF00' : status === 'busy' ? '#FF0000' : '#808080',
            fillOpacity: 0.8,
            strokeWeight: 2,
            strokeColor: '#FFFFFF'
        };
    }
    
    /**
     * Create content for info window
     */
    createInfoWindowContent(info) {
        const lastUpdate = info.lastUpdate ? new Date(info.lastUpdate).toLocaleString() : 'Unknown';
        const currentJob = info.currentJob ? `
            <p><strong>Current Job:</strong> ${info.currentJob.parcel_tracking} (${info.currentJob.job_type})</p>
            <p><strong>Status:</strong> ${info.currentJob.status}</p>
        ` : '<p><strong>Status:</strong> No active job</p>';
        
        return `
            <div style="max-width: 250px;">
                <h4>${info.driverName || 'Driver'}</h4>
                <p><strong>Last Update:</strong> ${lastUpdate}</p>
                <p><strong>Accuracy:</strong> ${info.accuracy ? Math.round(info.accuracy) + 'm' : 'Unknown'}</p>
                ${currentJob}
                ${info.speed ? `<p><strong>Speed:</strong> ${Math.round(info.speed)} km/h</p>` : ''}
            </div>
        `;
    }
    
    /**
     * Center map on specific driver
     */
    centerOnDriver(driverId) {
        if (this.driverMarkers.has(driverId)) {
            const marker = this.driverMarkers.get(driverId);
            this.map.setCenter(marker.getPosition());
            this.map.setZoom(15);
        }
    }
    
    /**
     * Fit map to show all drivers
     */
    fitToAllDrivers() {
        if (this.driverMarkers.size === 0) return;
        
        const bounds = new google.maps.LatLngBounds();
        this.driverMarkers.forEach(marker => {
            bounds.extend(marker.getPosition());
        });
        
        this.map.fitBounds(bounds);
    }
    
    /**
     * Start automatic updates
     */
    startAutoUpdate(updateFunction, intervalSeconds = 30) {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        this.updateInterval = setInterval(() => {
            updateFunction();
        }, intervalSeconds * 1000);
        
        // Initial update
        updateFunction();
    }
    
    /**
     * Stop automatic updates
     */
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    /**
     * Clear all markers and routes
     */
    clearAll() {
        this.driverMarkers.forEach(marker => marker.setMap(null));
        this.routePolylines.forEach(polyline => polyline.setMap(null));
        this.infoWindows.forEach(infoWindow => infoWindow.close());
        
        this.driverMarkers.clear();
        this.routePolylines.clear();
        this.infoWindows.clear();
    }
}

/**
 * Admin Dashboard Map Controller
 */
class AdminDashboardMap {
    constructor(containerId) {
        this.map = new DriverTrackingMap(containerId, {
            zoom: 8,
            center: { lat: 52.5200, lng: 1.4050 } // UK center
        });
        
        this.selectedDriverId = null;
        this.showRoutes = false;
        
        this.initializeControls();
        this.startTracking();
    }
    
    initializeControls() {
        // Add map controls
        const controlsContainer = document.createElement('div');
        controlsContainer.className = 'map-controls';
        controlsContainer.innerHTML = `
            <div class="btn-group" role="group">
                <button type="button" class="btn btn-sm btn-primary" id="fitAllDrivers">
                    Fit All Drivers
                </button>
                <button type="button" class="btn btn-sm btn-secondary" id="toggleRoutes">
                    Toggle Routes
                </button>
                <button type="button" class="btn btn-sm btn-info" id="refreshLocations">
                    Refresh
                </button>
            </div>
        `;
        
        // Add controls to map
        if (this.map.isInitialized) {
            this.map.map.controls[google.maps.ControlPosition.TOP_RIGHT].push(controlsContainer);
        }
        
        // Bind control events
        document.getElementById('fitAllDrivers')?.addEventListener('click', () => {
            this.map.fitToAllDrivers();
        });
        
        document.getElementById('toggleRoutes')?.addEventListener('click', () => {
            this.toggleRouteDisplay();
        });
        
        document.getElementById('refreshLocations')?.addEventListener('click', () => {
            this.updateDriverLocations();
        });
    }
    
    startTracking() {
        this.map.startAutoUpdate(() => {
            this.updateDriverLocations();
        }, 30); // Update every 30 seconds
    }
    
    async updateDriverLocations() {
        try {
            const response = await fetch('/api/admin/drivers/locations/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displayDrivers(data.drivers);
                this.updateDriversList(data.drivers);
            } else {
                console.error('Failed to fetch driver locations');
            }
        } catch (error) {
            console.error('Error fetching driver locations:', error);
        }
    }
    
    displayDrivers(drivers) {
        // Clear existing markers
        this.map.clearAll();
        
        // Add markers for each driver
        drivers.forEach(driver => {
            if (driver.latitude && driver.longitude) {
                this.map.updateDriverLocation(driver.driver_id, {
                    latitude: driver.latitude,
                    longitude: driver.longitude
                }, {
                    driverName: driver.username,
                    lastUpdate: driver.last_update,
                    accuracy: driver.accuracy,
                    status: driver.is_available ? 'available' : 'busy',
                    currentJob: driver.current_job
                });
            }
        });
        
        // Fit map to show all drivers
        if (drivers.length > 0) {
            this.map.fitToAllDrivers();
        }
    }
    
    updateDriversList(drivers) {
        const driversListContainer = document.getElementById('drivers-list');
        if (!driversListContainer) return;
        
        driversListContainer.innerHTML = drivers.map(driver => `
            <div class="driver-item" data-driver-id="${driver.driver_id}">
                <div class="driver-info">
                    <h6>${driver.username}</h6>
                    <small class="text-muted">
                        Last update: ${driver.last_update ? new Date(driver.last_update).toLocaleString() : 'Never'}
                    </small>
                </div>
                <div class="driver-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="adminMap.centerOnDriver(${driver.driver_id})">
                        View
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="adminMap.toggleDriverRoute(${driver.driver_id})">
                        Route
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    centerOnDriver(driverId) {
        this.map.centerOnDriver(driverId);
        this.selectedDriverId = driverId;
    }
    
    async toggleDriverRoute(driverId) {
        if (this.map.routePolylines.has(driverId)) {
            this.map.hideDriverRoute(driverId);
        } else {
            await this.showDriverRoute(driverId);
        }
    }
    
    async showDriverRoute(driverId) {
        try {
            const response = await fetch(`/api/driver/${driverId}/route-history/?hours=8`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.route_history && data.route_history.length > 0) {
                    this.map.showDriverRoute(driverId, data.route_history, {
                        color: '#0066CC',
                        weight: 4
                    });
                }
            }
        } catch (error) {
            console.error('Error fetching driver route:', error);
        }
    }
    
    toggleRouteDisplay() {
        this.showRoutes = !this.showRoutes;
        
        if (this.showRoutes) {
            // Show routes for all drivers
            this.map.driverMarkers.forEach((marker, driverId) => {
                this.showDriverRoute(driverId);
            });
        } else {
            // Hide all routes
            this.map.routePolylines.forEach((polyline, driverId) => {
                this.map.hideDriverRoute(driverId);
            });
        }
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

/**
 * Customer Tracking Map Controller
 */
class CustomerTrackingMap {
    constructor(containerId, trackingNumber) {
        this.map = new DriverTrackingMap(containerId, {
            zoom: 12
        });
        
        this.trackingNumber = trackingNumber;
        this.driverMarker = null;
        this.deliveryMarker = null;
        
        this.startTracking();
    }
    
    startTracking() {
        this.map.startAutoUpdate(() => {
            this.updateDriverLocation();
        }, 60); // Update every minute for customers
    }
    
    async updateDriverLocation() {
        try {
            const response = await fetch(`/api/customer/track/${this.trackingNumber}/location/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.tracking_available && data.driver_location) {
                    this.displayDriverLocation(data);
                } else {
                    this.showTrackingUnavailable(data.message);
                }
            } else {
                console.error('Failed to fetch driver location');
            }
        } catch (error) {
            console.error('Error fetching driver location:', error);
        }
    }
    
    displayDriverLocation(data) {
        const driverLocation = data.driver_location;
        
        // Update driver marker
        this.map.updateDriverLocation('customer_driver', {
            latitude: driverLocation.latitude,
            longitude: driverLocation.longitude
        }, {
            driverName: 'Your Delivery Driver',
            lastUpdate: driverLocation.last_update,
            accuracy: driverLocation.accuracy,
            status: 'busy',
            currentJob: {
                parcel_tracking: this.trackingNumber,
                job_type: data.job_info.job_type,
                status: data.job_info.status
            }
        });
        
        // Center map on driver
        this.map.centerOnDriver('customer_driver');
        
        // Update tracking info
        this.updateTrackingInfo(data);
    }
    
    updateTrackingInfo(data) {
        const trackingInfoContainer = document.getElementById('tracking-info');
        if (!trackingInfoContainer) return;
        
        const eta = data.job_info.estimated_arrival ? 
            new Date(data.job_info.estimated_arrival).toLocaleString() : 'Calculating...';
        
        trackingInfoContainer.innerHTML = `
            <div class="alert alert-info">
                <h5>Live Tracking Active</h5>
                <p><strong>Status:</strong> ${data.parcel_status}</p>
                <p><strong>Driver Status:</strong> ${data.job_info.status}</p>
                <p><strong>Estimated Arrival:</strong> ${eta}</p>
                <p><strong>Last Update:</strong> ${new Date(data.driver_location.last_update).toLocaleString()}</p>
            </div>
        `;
    }
    
    showTrackingUnavailable(message) {
        const trackingInfoContainer = document.getElementById('tracking-info');
        if (!trackingInfoContainer) return;
        
        trackingInfoContainer.innerHTML = `
            <div class="alert alert-warning">
                <h5>Live Tracking Unavailable</h5>
                <p>${message}</p>
            </div>
        `;
    }
}

// Global variables for map instances
let adminMap = null;
let customerMap = null;

// Initialize maps when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize admin dashboard map
    if (document.getElementById('admin-map')) {
        adminMap = new AdminDashboardMap('admin-map');
    }
    
    // Initialize customer tracking map
    const customerMapContainer = document.getElementById('customer-map');
    if (customerMapContainer) {
        const trackingNumber = customerMapContainer.dataset.trackingNumber;
        if (trackingNumber) {
            customerMap = new CustomerTrackingMap('customer-map', trackingNumber);
        }
    }
});

// Utility function to load Google Maps API
function loadGoogleMapsAPI(apiKey) {
    if (typeof google !== 'undefined' && google.maps) {
        return Promise.resolve();
    }
    
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&callback=initGoogleMaps`;
        script.async = true;
        script.defer = true;
        
        window.initGoogleMaps = function() {
            resolve();
        };
        
        script.onerror = function() {
            reject(new Error('Failed to load Google Maps API'));
        };
        
        document.head.appendChild(script);
    });
}

