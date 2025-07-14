// Real-time tracking and notifications
class RealTimeTracker {
    constructor() {
        this.pollingInterval = 30000; // 30 seconds
        this.isPolling = false;
        this.intervalId = null;
    }

    startPolling(trackingNumber) {
        if (this.isPolling) {
            this.stopPolling();
        }

        this.isPolling = true;
        this.intervalId = setInterval(() => {
            this.updateTrackingInfo(trackingNumber);
        }, this.pollingInterval);

        // Initial update
        this.updateTrackingInfo(trackingNumber);
    }

    stopPolling() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isPolling = false;
    }

    async updateTrackingInfo(trackingNumber) {
        try {
            const response = await fetch(`/api/public/track/${trackingNumber}/`);
            if (response.ok) {
                const data = await response.json();
                this.updateTrackingDisplay(data);
                this.showNotification('Tracking Updated', 'Latest tracking information loaded');
            }
        } catch (error) {
            console.error('Error updating tracking info:', error);
        }
    }

    updateTrackingDisplay(parcelData) {
        // Update status badge
        const statusElements = document.querySelectorAll('.parcel-status');
        statusElements.forEach(element => {
            element.textContent = this.formatStatus(parcelData.status);
            element.className = `status-badge status-${parcelData.status}`;
        });

        // Update timeline if present
        const timelineContainer = document.getElementById('trackingTimeline');
        if (timelineContainer && parcelData.tracking_events) {
            this.updateTimeline(timelineContainer, parcelData.tracking_events);
        }
    }

    updateTimeline(container, events) {
        container.innerHTML = `
            <h5>Tracking History</h5>
            <div class="tracking-timeline">
                ${events.map(event => `
                    <div class="timeline-item">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6>${event.status_update}</h6>
                                <p class="text-muted mb-1">${event.notes}</p>
                                ${event.location ? `<small class="text-muted"><i class="fas fa-map-marker-alt me-1"></i>${event.location}</small>` : ''}
                            </div>
                            <small class="text-muted">${this.formatDateTime(event.timestamp)}</small>
                        </div>
                        ${event.image ? `<img src="${event.image}" class="img-thumbnail mt-2" style="max-width: 200px;">` : ''}
                        ${event.signature ? `<img src="${event.signature}" class="img-thumbnail mt-2" style="max-width: 200px;">` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    showNotification(title, message) {
        // Check if browser supports notifications
        if ('Notification' in window) {
            if (Notification.permission === 'granted') {
                new Notification(title, {
                    body: message,
                    icon: '/static/tracking/images/logo.png'
                });
            } else if (Notification.permission !== 'denied') {
                Notification.requestPermission().then(permission => {
                    if (permission === 'granted') {
                        new Notification(title, {
                            body: message,
                            icon: '/static/tracking/images/logo.png'
                        });
                    }
                });
            }
        }

        // Also show in-page notification
        this.showInPageNotification(title, message);
    }

    showInPageNotification(title, message) {
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show position-fixed';
        notification.style.cssText = 'top: 100px; right: 20px; z-index: 9999; max-width: 300px;';
        notification.innerHTML = `
            <strong>${title}</strong><br>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    formatStatus(status) {
        return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    formatDateTime(dateString) {
        return new Date(dateString).toLocaleString();
    }
}

// Notification Manager
class NotificationManager {
    constructor() {
        this.lastNotificationCheck = Date.now();
        this.checkInterval = 60000; // 1 minute
    }

    startNotificationPolling() {
        setInterval(() => {
            this.checkForNewNotifications();
        }, this.checkInterval);
    }

    async checkForNewNotifications() {
        try {
            const response = await fetch('/api/notifications/');
            if (response.ok) {
                const data = await response.json();
                const notifications = data.results || data;
                
                // Filter new notifications
                const newNotifications = notifications.filter(n => 
                    !n.is_read && new Date(n.created_at).getTime() > this.lastNotificationCheck
                );

                newNotifications.forEach(notification => {
                    this.showNotification(notification);
                });

                this.lastNotificationCheck = Date.now();
            }
        } catch (error) {
            console.error('Error checking notifications:', error);
        }
    }

    showNotification(notification) {
        const tracker = new RealTimeTracker();
        tracker.showNotification(notification.title, notification.message);
    }
}

// Global instances
window.realTimeTracker = new RealTimeTracker();
window.notificationManager = new NotificationManager();

// Auto-start notification polling if user is logged in
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated by looking for user-specific elements
    const userElements = document.querySelectorAll('[data-user-authenticated]');
    if (userElements.length > 0) {
        window.notificationManager.startNotificationPolling();
    }

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

