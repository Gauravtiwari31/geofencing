// SOS functionality for Tourist Mobile Simulator

class SOSController {
    constructor() {
        this.isActive = false;
        this.button = null;
        this.statusElement = null;
        this.lastSOSTime = null;
        this.initialize();
    }

    initialize() {
        this.button = document.getElementById('sos-btn');
        this.statusElement = document.getElementById('sos-status');

        if (this.button) {
            this.button.addEventListener('click', () => this.toggleSOS());
        }

        console.log('SOS controller initialized');
    }

    async toggleSOS() {
        if (!mapController) {
            addLogEntry('Map not initialized', 'error');
            return;
        }

        const currentLocation = mapController.getCurrentLocation();
        if (!currentLocation) {
            addLogEntry('No location set - click on map first', 'error');
            return;
        }

        if (this.isActive) {
            this.deactivateSOS();
        } else {
            await this.activateSOS(currentLocation);
        }
    }

    async activateSOS(location) {
        try {
            // Show confirmation dialog
            const confirmed = confirm(
                '🚨 EMERGENCY ALERT 🚨\n\n' +
                'This will send an SOS alert to emergency services.\n' +
                `Location: ${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}\n\n` +
                'Are you sure you want to proceed?'
            );

            if (!confirmed) {
                return;
            }

            // Disable button temporarily
            this.button.disabled = true;
            this.updateStatus('Sending SOS...', 'warning');

            // Send SOS to backend
            const response = await fetch('/api/sos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    lat: location.lat,
                    lng: location.lng
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.isActive = true;
                this.lastSOSTime = new Date();
                this.updateButton();
                this.updateStatus('SOS ACTIVE - Emergency services notified', 'error');
                
                addLogEntry(
                    `🚨 SOS ACTIVATED at ${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}`,
                    'error'
                );

                // Flash the button
                this.flashButton();

                console.log('SOS activated:', result);
            } else {
                const error = await response.text();
                this.updateStatus('SOS failed to send', 'error');
                addLogEntry(`SOS failed: ${error}`, 'error');
                console.error('SOS failed:', error);
            }
        } catch (error) {
            this.updateStatus('SOS error', 'error');
            addLogEntry(`SOS error: ${error.message}`, 'error');
            console.error('SOS error:', error);
        } finally {
            this.button.disabled = false;
        }
    }

    deactivateSOS() {
        this.isActive = false;
        this.updateButton();
        this.updateStatus('SOS Deactivated', 'success');
        addLogEntry('SOS deactivated', 'warning');
    }

    updateButton() {
        if (!this.button) return;

        if (this.isActive) {
            this.button.classList.add('active');
            this.button.querySelector('.sos-text').textContent = 'ACTIVE';
        } else {
            this.button.classList.remove('active');
            this.button.querySelector('.sos-text').textContent = 'SOS';
        }
    }

    updateStatus(message, type = 'info') {
        if (!this.statusElement) return;

        this.statusElement.textContent = message;
        this.statusElement.className = `sos-status ${type}`;
    }

    flashButton() {
        if (!this.button) return;

        let flashCount = 0;
        const flashInterval = setInterval(() => {
            this.button.style.opacity = this.button.style.opacity === '0.5' ? '1' : '0.5';
            flashCount++;

            if (flashCount >= 6) { // Flash 3 times
                clearInterval(flashInterval);
                this.button.style.opacity = '1';
            }
        }, 250);
    }

    getStatus() {
        return {
            active: this.isActive,
            lastActivated: this.lastSOSTime
        };
    }

    reset() {
        this.isActive = false;
        this.lastSOSTime = null;
        this.updateButton();
        this.updateStatus('SOS Ready', 'info');
    }
}

// Global SOS controller instance
let sosController = null;

// Initialize SOS when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    sosController = new SOSController();
});

// Utility functions
function getSOSStatus() {
    return sosController ? sosController.getStatus() : { active: false };
}

function resetSOS() {
    if (sosController) {
        sosController.reset();
    }
}
