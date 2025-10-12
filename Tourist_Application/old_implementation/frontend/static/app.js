// Main application logic for Tourist Mobile Simulator

class TouristApp {
    constructor() {
        this.isAuthenticated = false;
        this.currentUser = null;
        this.statusCheckInterval = null;
        this.simulationCheckInterval = null;
        this.availablePaths = {};
        this.keycloak = {
            url: 'https://localhost:2027',
            realm: 'mod-core',
            clientId: 'tourist-app',
            redirectUri: 'http://localhost:2040/auth/callback'
        };
        this.initialize();
    }

    // PKCE helpers
    async generateCodeVerifier() {
        const array = new Uint8Array(64);
        crypto.getRandomValues(array);
        return btoa(String.fromCharCode.apply(null, array)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }

    async sha256(plain) {
        const encoder = new TextEncoder();
        const data = encoder.encode(plain);
        const hash = await crypto.subtle.digest('SHA-256', data);
        return hash;
    }

    base64UrlEncode(arrayBuffer) {
        const bytes = new Uint8Array(arrayBuffer);
        let binary = '';
        bytes.forEach((b) => binary += String.fromCharCode(b));
        return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }

    async loginWithKeycloak() {
        try {
            const state = crypto.randomUUID();
            const verifier = await this.generateCodeVerifier();
            const challenge = this.base64UrlEncode(await this.sha256(verifier));

            sessionStorage.setItem('oauth_state', state);
            sessionStorage.setItem('pkce_verifier', verifier);

            const authUrl = `${this.keycloak.url}/realms/${this.keycloak.realm}/protocol/openid-connect/auth` +
                `?client_id=${encodeURIComponent(this.keycloak.clientId)}` +
                `&response_type=code` +
                `&scope=${encodeURIComponent('openid profile email')}` +
                `&redirect_uri=${encodeURIComponent(this.keycloak.redirectUri)}` +
                `&state=${encodeURIComponent(state)}` +
                `&code_challenge=${encodeURIComponent(challenge)}` +
                `&code_challenge_method=S256`;

            window.location.href = authUrl;
        } catch (e) {
            addLogEntry(`Login init error: ${e.message}`, 'error');
        }
    }

    async handleAuthCallbackIfPresent() {
        try {
            const url = new URL(window.location.href);
            if (url.pathname !== '/auth/callback') return;

            const code = url.searchParams.get('code');
            const state = url.searchParams.get('state');
            const storedState = sessionStorage.getItem('oauth_state');
            const verifier = sessionStorage.getItem('pkce_verifier');

            if (!code || !state || !storedState || !verifier) {
                addLogEntry('Missing code/state/verifier for token exchange', 'error');
                return;
            }
            if (state !== storedState) {
                addLogEntry('Invalid state parameter', 'error');
                return;
            }

            const body = new URLSearchParams({
                grant_type: 'authorization_code',
                client_id: this.keycloak.clientId,
                code,
                redirect_uri: this.keycloak.redirectUri,
                code_verifier: verifier
            });

            const tokenResp = await fetch(`${this.keycloak.url}/realms/${this.keycloak.realm}/protocol/openid-connect/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body
            });

            if (!tokenResp.ok) {
                const txt = await tokenResp.text();
                addLogEntry(`Token exchange failed: ${txt}`, 'error');
                return;
            }

            const tokens = await tokenResp.json();
            sessionStorage.setItem('access_token', tokens.access_token);
            sessionStorage.setItem('refresh_token', tokens.refresh_token);

            addLogEntry('Interactive login succeeded', 'success');
            // Strip code/state from URL
            window.history.replaceState({}, document.title, '/');
            this.checkAuthStatus();
        } catch (e) {
            addLogEntry(`Callback error: ${e.message}`, 'error');
        }
    }

    setupEventHandlers() {
        // Authentication buttons
        const loginBtn = document.getElementById('login-btn');
        const refreshBtn = document.getElementById('refresh-btn');
        
        if (loginBtn) {
            loginBtn.addEventListener('click', () => this.loginWithKeycloak());
        }
        
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshToken());
        }

        // Simulation controls
        const startSimBtn = document.getElementById('start-sim-btn');
        const stopSimBtn = document.getElementById('stop-sim-btn');
        const pathSelect = document.getElementById('path-select');
        
        if (startSimBtn) {
            startSimBtn.addEventListener('click', () => this.startSimulation());
        }
        
        if (stopSimBtn) {
            stopSimBtn.addEventListener('click', () => this.stopSimulation());
        }

        if (pathSelect) {
            pathSelect.addEventListener('change', () => this.onPathSelectionChange());
        }

        // Device controls
        const registerDeviceBtn = document.getElementById('register-device-btn');
        if (registerDeviceBtn) {
            registerDeviceBtn.addEventListener('click', () => this.registerDevice());
        }
    }

    startHeartbeat() {
        if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
        this.heartbeatInterval = setInterval(async () => {
            try {
                // Use last map location if available; otherwise no-op
                if (!mapController || !mapController.getCurrentLocation) return;
                const loc = mapController.getCurrentLocation();
                if (!loc || typeof loc.lat !== 'number' || typeof loc.lon === 'number' && isNaN(loc.lon)) return;
                // Normalize fields to lat/lng
                const lat = loc.lat;
                const lng = loc.lng !== undefined ? loc.lng : loc.lon;

                const token = sessionStorage.getItem('access_token');
                const headers = { 'Content-Type': 'application/json' };
                if (token) headers['Authorization'] = `Bearer ${token}`;

                await fetch('/api/location', {
                    method: 'POST',
                    headers,
                    body: JSON.stringify({ lat, lng })
                });

                addLogEntry(`Heartbeat sent: ${lat.toFixed(5)}, ${lng.toFixed(5)}`, 'info');
            } catch (e) {
                addLogEntry(`Heartbeat error: ${e.message}`, 'error');
            }
        }, 5000);
    }

    initialize() {
        // Wire up UI and begin status flows
        this.setupEventHandlers();
        // If we just returned from Keycloak, finish the PKCE exchange
        this.handleAuthCallbackIfPresent();
        // Start background status checks and load data
        this.startStatusChecking();
        this.loadAvailablePaths();
        this.checkAuthStatus();
        // Start heartbeat to MoD Core via backend
        this.startHeartbeat();
        // Log startup
        console.log('Tourist App initialized');
        addLogEntry('Tourist Mobile Simulator started');
    }

    async login() {
        try {
            window.location.href = '/auth/login';
        } catch (error) {
            addLogEntry(`Login error: ${error.message}`, 'error');
        }
    }

    async refreshToken() {
        // Try frontend refresh first
        const refreshToken = sessionStorage.getItem('refresh_token');
        if (refreshToken) {
            const body = new URLSearchParams({
                grant_type: 'refresh_token',
                client_id: this.keycloak.clientId,
                refresh_token: refreshToken
            });
            const tokenResp = await fetch(`${this.keycloak.url}/realms/${this.keycloak.realm}/protocol/openid-connect/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body
            });
            if (tokenResp.ok) {
                const tokens = await tokenResp.json();
                sessionStorage.setItem('access_token', tokens.access_token);
                sessionStorage.setItem('refresh_token', tokens.refresh_token);
                addLogEntry('Token refreshed (frontend)', 'success');
                this.checkAuthStatus();
                return;
            }
        }
        // fallback to backend refresh
        try {
            const response = await fetch('/auth/refresh', { method: 'POST' });
            
            if (response.ok) {
                addLogEntry('Token refreshed successfully', 'success');
                this.checkAuthStatus();
            } else {
                const error = await response.text();
                addLogEntry(`Token refresh failed: ${error}`, 'error');
            }
        } catch (error) {
            addLogEntry(`Token refresh error: ${error.message}`, 'error');
        }
    }

    async checkAuthStatus() {
        // Prefer frontend token if present
        const token = sessionStorage.getItem('access_token');
        if (token) {
            this.isAuthenticated = true;
            const authText = document.getElementById('auth-text');
            if (authText) authText.textContent = 'Authenticated (frontend)';
            const refreshBtn = document.getElementById('refresh-btn');
            if (refreshBtn) refreshBtn.disabled = false;
            return;
        }
        // fallback to backend status
        try {
            const response = await fetch('/auth/status');
            
            if (response.ok) {
                const authStatus = await response.json();
                this.updateAuthStatus(authStatus);
            } else {
                this.updateAuthStatus({ authenticated: false });
            }
        } catch (error) {
            console.error('Auth status check failed:', error);
            this.updateAuthStatus({ authenticated: false });
        }
    }

    updateAuthStatus(authStatus) {
        this.isAuthenticated = authStatus.authenticated;
        this.currentUser = authStatus.user_id;

        const authText = document.getElementById('auth-text');
        const refreshBtn = document.getElementById('refresh-btn');
        const registerDeviceBtn = document.getElementById('register-device-btn');
        const userInfo = document.getElementById('user-info');

        if (authText) {
            authText.textContent = this.isAuthenticated ? 'Authenticated' : 'Not Authenticated';
        }

        if (refreshBtn) {
            refreshBtn.disabled = !this.isAuthenticated;
        }

        if (registerDeviceBtn) {
            registerDeviceBtn.disabled = !this.isAuthenticated;
        }

        if (userInfo) {
            userInfo.textContent = this.isAuthenticated ? 
                `User: ${this.currentUser || 'Unknown'}` : 
                'Please login to continue';
        }

        // Enable/disable simulation based on auth
        this.updateSimulationControls();
    }

    async loadAvailablePaths() {
        try {
            const response = await fetch('/api/simulate/paths');
            
            if (response.ok) {
                const data = await response.json();
                this.availablePaths = data.paths;
                this.populatePathSelect();
            }
        } catch (error) {
            console.error('Failed to load paths:', error);
        }
    }

    populatePathSelect() {
        const pathSelect = document.getElementById('path-select');
        if (!pathSelect) return;

        // Clear existing options except first
        pathSelect.innerHTML = '<option value="">Select a path...</option>';

        // Add available paths
        Object.entries(this.availablePaths).forEach(([key, path]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = `${path.name} (${path.points} points, ${path.speed}x speed)`;
            pathSelect.appendChild(option);
        });
    }

    onPathSelectionChange() {
        const pathSelect = document.getElementById('path-select');
        const startSimBtn = document.getElementById('start-sim-btn');

        if (pathSelect && startSimBtn) {
            const hasSelection = pathSelect.value !== '';
            startSimBtn.disabled = !hasSelection || !this.isAuthenticated;
        }
    }

    updateSimulationControls() {
        const startSimBtn = document.getElementById('start-sim-btn');
        const pathSelect = document.getElementById('path-select');

        if (startSimBtn && pathSelect) {
            const hasSelection = pathSelect.value !== '';
            startSimBtn.disabled = !hasSelection || !this.isAuthenticated;
        }
    }

    async startSimulation() {
        const pathSelect = document.getElementById('path-select');
        if (!pathSelect || !pathSelect.value) {
            addLogEntry('Please select a path first', 'error');
            return;
        }

        try {
            const response = await fetch('/api/simulate/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path_name: pathSelect.value })
            });

            if (response.ok) {
                const result = await response.json();
                addLogEntry(`Simulation started: ${result.message}`, 'success');
                this.updateSimulationUI(true);
                this.startSimulationMonitoring();
            } else {
                const error = await response.text();
                addLogEntry(`Simulation start failed: ${error}`, 'error');
            }
        } catch (error) {
            addLogEntry(`Simulation error: ${error.message}`, 'error');
        }
    }

    async stopSimulation() {
        try {
            const response = await fetch('/api/simulate/stop', { method: 'POST' });

            if (response.ok) {
                const result = await response.json();
                addLogEntry(`Simulation stopped: ${result.message}`, 'success');
                this.updateSimulationUI(false);
                this.stopSimulationMonitoring();
            } else {
                const error = await response.text();
                addLogEntry(`Simulation stop failed: ${error}`, 'error');
            }
        } catch (error) {
            addLogEntry(`Simulation stop error: ${error.message}`, 'error');
        }
    }

    updateSimulationUI(isRunning) {
        const startSimBtn = document.getElementById('start-sim-btn');
        const stopSimBtn = document.getElementById('stop-sim-btn');
        const pathSelect = document.getElementById('path-select');

        if (startSimBtn) startSimBtn.disabled = isRunning || !this.isAuthenticated;
        if (stopSimBtn) stopSimBtn.disabled = !isRunning;
        if (pathSelect) pathSelect.disabled = isRunning;
    }

    startSimulationMonitoring() {
        if (this.simulationCheckInterval) {
            clearInterval(this.simulationCheckInterval);
        }

        this.simulationCheckInterval = setInterval(() => {
            this.checkSimulationStatus();
        }, 2000);
    }

    stopSimulationMonitoring() {
        if (this.simulationCheckInterval) {
            clearInterval(this.simulationCheckInterval);
            this.simulationCheckInterval = null;
        }

        // Reset progress display
        this.updateSimulationProgress(0, 'No simulation running');
    }

    async checkSimulationStatus() {
        try {
            const response = await fetch('/api/simulate/status');
            
            if (response.ok) {
                const status = await response.json();
                
                if (status.active) {
                    const progressPercent = (status.progress * 100).toFixed(1);
                    this.updateSimulationProgress(
                        status.progress,
                        `${status.path_name}: ${progressPercent}% complete`
                    );

                    // Update map if location available
                    if (status.current_position && mapController) {
                        mapController.setLocation(
                            status.current_position.lat,
                            status.current_position.lng
                        );
                    }
                } else {
                    this.updateSimulationUI(false);
                    this.stopSimulationMonitoring();
                }
            }
        } catch (error) {
            console.error('Simulation status check failed:', error);
        }
    }

    updateSimulationProgress(progress, text) {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');

        if (progressFill) {
            progressFill.style.width = `${progress * 100}%`;
        }

        if (progressText) {
            progressText.textContent = text;
        }
    }

    async registerDevice() {
        try {
            const response = await fetch('/api/device/register', { method: 'POST' });

            if (response.ok) {
                const result = await response.json();
                addLogEntry('Device registered successfully', 'success');
                console.log('Device registration result:', result);
            } else {
                const error = await response.text();
                addLogEntry(`Device registration failed: ${error}`, 'error');
            }
        } catch (error) {
            addLogEntry(`Device registration error: ${error.message}`, 'error');
        }
    }

    startStatusChecking() {
        // Initial status check
        this.checkAppStatus();

        // Set up periodic checking
        this.statusCheckInterval = setInterval(() => {
            this.checkAppStatus();
        }, 10000); // Check every 10 seconds
    }

    async checkAppStatus() {
        try {
            const response = await fetch('/api/status');
            
            if (response.ok) {
                const status = await response.json();
                this.updateConnectionStatus(status.connection);
                this.updateDeviceStatus(status);
            }
        } catch (error) {
            console.error('Status check failed:', error);
        }
    }

    updateConnectionStatus(connectionStatus) {
        const connectionText = document.getElementById('connection-text');
        
        if (connectionText) {
            const status = connectionStatus.gateway_connected ? 'Connected' : 'Disconnected';
            connectionText.textContent = status;
        }
    }

    updateDeviceStatus(appStatus) {
        const mqttStatus = document.getElementById('mqtt-status');
        const gatewayStatus = document.getElementById('gateway-status');

        if (mqttStatus) {
            mqttStatus.textContent = appStatus.connection.mqtt_connected ? 'Connected' : 'Disconnected';
            mqttStatus.className = `status-indicator ${appStatus.connection.mqtt_connected ? 'connected' : 'disconnected'}`;
        }

        if (gatewayStatus) {
            gatewayStatus.textContent = appStatus.connection.gateway_connected ? 'Connected' : 'Disconnected';
            gatewayStatus.className = `status-indicator ${appStatus.connection.gateway_connected ? 'connected' : 'disconnected'}`;
        }
    }

    cleanup() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }
        if (this.simulationCheckInterval) {
            clearInterval(this.simulationCheckInterval);
        }
    }
}

// Global app instance
let touristApp = null;

// Activity log utility
function addLogEntry(message, type = 'info') {
    const logContainer = document.getElementById('activity-log');
    if (!logContainer) return;

    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;

    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;

    // Limit log entries to last 50
    const entries = logContainer.querySelectorAll('.log-entry');
    if (entries.length > 50) {
        entries[0].remove();
    }

    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Make addLogEntry globally available
window.addLogEntry = addLogEntry;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    touristApp = new TouristApp();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (touristApp) {
        touristApp.cleanup();
    }
});
