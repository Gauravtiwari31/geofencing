// Map functionality for Tourist Mobile Simulator using Leaflet

class MapController {
    constructor() {
        this.map = null;
        this.currentMarker = null;
        this.pathLayer = null;
        this.currentLocation = { lat: 26.1625, lng: 91.7794 }; // Default to Guwahati
        this.initialize();
    }

    initialize() {
        // Initialize Leaflet map - Start with India view
        this.map = L.map('map').setView([20.5937, 78.9629], 5); // Center of India, zoom level 5

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19,
            minZoom: 3
        }).addTo(this.map);

        // Add click handler
        this.map.on('click', (e) => this.onMapClick(e));

        // Force map to refresh after container is ready
        setTimeout(() => {
            this.map.invalidateSize();
        }, 100);

        console.log('Leaflet map initialized with India view');
    }

    onMapClick(e) {
        const lat = e.latlng.lat;
        const lng = e.latlng.lng;
        
        this.setLocation(lat, lng);
        this.sendLocationToBackend(lat, lng);
    }

    setLocation(lat, lng) {
        this.currentLocation = { lat, lng };
        
        // Remove existing marker
        if (this.currentMarker) {
            this.map.removeLayer(this.currentMarker);
        }

        // Add new marker
        this.currentMarker = L.marker([lat, lng]).addTo(this.map);
        this.currentMarker.bindPopup(`
            <div style="font-family: Arial, sans-serif; text-align: center;">
                <h4 style="margin: 0 0 10px 0; color: #333;">📍 Current Location</h4>
                <p style="margin: 5px 0; font-size: 14px;"><strong>Latitude:</strong> ${lat.toFixed(6)}</p>
                <p style="margin: 5px 0; font-size: 14px;"><strong>Longitude:</strong> ${lng.toFixed(6)}</p>
                <p style="margin: 10px 0 0 0; font-size: 12px; color: #666; font-style: italic;">Click elsewhere to move location</p>
            </div>
        `).openPopup();

        // Update coordinate display
        this.updateCoordinateDisplay(lat, lng);

        // Enable SOS button now that we have a location
        this.enableSOSButton();

        console.log(`Location set to: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
    }

    updateCoordinateDisplay(lat, lng) {
        const coordsElement = document.getElementById('current-coords');
        if (coordsElement) {
            coordsElement.textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
        }
    }

    enableSOSButton() {
        const sosButton = document.getElementById('sos-btn');
        if (sosButton) {
            sosButton.disabled = false;
        }
        
        // Also enable zoom to location button
        const zoomBtn = document.getElementById('zoom-location-btn');
        if (zoomBtn) {
            zoomBtn.disabled = false;
        }
    }

    resetToIndiaView() {
        this.map.setView([20.5937, 78.9629], 5); // Center of India, zoom level 5
        console.log('Map reset to India view');
    }

    zoomToCurrentLocation() {
        if (this.currentLocation) {
            this.map.setView([this.currentLocation.lat, this.currentLocation.lng], 13);
            console.log('Zoomed to current location');
        }
    }

    async sendLocationToBackend(lat, lng) {
        try {
            const response = await fetch('/api/location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ lat, lng })
            });

            if (response.ok) {
                const result = await response.json();
                addLogEntry(`Location sent successfully: ${lat.toFixed(6)}, ${lng.toFixed(6)}`, 'success');
                console.log('Location sent:', result);
            } else {
                const error = await response.text();
                addLogEntry(`Failed to send location: ${error}`, 'error');
                console.error('Failed to send location:', error);
            }
        } catch (error) {
            addLogEntry(`Location send error: ${error.message}`, 'error');
            console.error('Location send error:', error);
        }
    }

    drawPath(coordinates) {
        // Remove existing path
        if (this.pathLayer) {
            this.map.removeLayer(this.pathLayer);
        }

        // Create polyline
        this.pathLayer = L.polyline(coordinates, {
            color: '#667eea',
            weight: 4,
            opacity: 0.7
        }).addTo(this.map);

        // Fit map to path bounds
        this.map.fitBounds(this.pathLayer.getBounds());

        console.log('Path drawn with', coordinates.length, 'points');
    }

    clearPath() {
        if (this.pathLayer) {
            this.map.removeLayer(this.pathLayer);
            this.pathLayer = null;
        }
    }

    panTo(lat, lng) {
        this.map.panTo([lat, lng]);
        this.setLocation(lat, lng);
    }

    getCurrentLocation() {
        return this.currentLocation;
    }
}

// Global map controller instance
let mapController = null;

// Initialize map when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    mapController = new MapController();
    
    // Set up manual location input
    setupLocationControls();
    
    // Set up preset location buttons
    setupPresetLocations();
});

function setupLocationControls() {
    const setLocationBtn = document.getElementById('set-location-btn');
    const latInput = document.getElementById('lat-input');
    const lngInput = document.getElementById('lng-input');
    const resetMapBtn = document.getElementById('reset-map-btn');
    const zoomLocationBtn = document.getElementById('zoom-location-btn');

    // Reset map to India view
    if (resetMapBtn) {
        resetMapBtn.addEventListener('click', () => {
            mapController.resetToIndiaView();
            addLogEntry('Map view reset to India', 'info');
        });
    }

    // Zoom to current location
    if (zoomLocationBtn) {
        zoomLocationBtn.addEventListener('click', () => {
            mapController.zoomToCurrentLocation();
            addLogEntry('Zoomed to current location', 'info');
        });
    }

    if (setLocationBtn && latInput && lngInput) {
        setLocationBtn.addEventListener('click', () => {
            const lat = parseFloat(latInput.value);
            const lng = parseFloat(lngInput.value);

            if (isNaN(lat) || isNaN(lng)) {
                addLogEntry('Invalid coordinates entered', 'error');
                return;
            }

            if (lat < -90 || lat > 90) {
                addLogEntry('Latitude must be between -90 and 90', 'error');
                return;
            }

            if (lng < -180 || lng > 180) {
                addLogEntry('Longitude must be between -180 and 180', 'error');
                return;
            }

            mapController.panTo(lat, lng);
            mapController.sendLocationToBackend(lat, lng);
            
            // Clear inputs
            latInput.value = '';
            lngInput.value = '';
        });

        // Allow Enter key to submit
        [latInput, lngInput].forEach(input => {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    setLocationBtn.click();
                }
            });
        });
    }
}

function setupPresetLocations() {
    const presetButtons = document.querySelectorAll('.preset-btn');
    
    presetButtons.forEach(button => {
        button.addEventListener('click', () => {
            const lat = parseFloat(button.dataset.lat);
            const lng = parseFloat(button.dataset.lng);
            
            if (!isNaN(lat) && !isNaN(lng)) {
                mapController.panTo(lat, lng);
                mapController.sendLocationToBackend(lat, lng);
                addLogEntry(`Moved to preset location: ${button.textContent}`, 'success');
            }
        });
    });
}

// Utility function to add log entries (defined in app.js)
function addLogEntry(message, type = 'info') {
    if (window.addLogEntry) {
        window.addLogEntry(message, type);
    } else {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}