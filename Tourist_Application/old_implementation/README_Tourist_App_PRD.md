# Tourist Mobile Application — Implementation Strategy & PRD

## Implementation Strategy

### Architecture Overview
The tourist mobile application runs as a containerized web application with:
- **Frontend**: Single-page web app with interactive map and SOS controls
- **Backend**: FastAPI service handling authentication, location forwarding, and MQTT bridging
- **Port**: 2040 (as specified in Dockerfile)
- **Communication**: Interfaces with Gateway on ports 2045 (API) and 2046 (MQTT)

### Technology Stack
- **Backend**: FastAPI (already in container), HTTPX for HTTP calls, Paho-MQTT for MQTT
- **Frontend**: Vanilla HTML/CSS/JS with Leaflet.js for mapping
- **Authentication**: Keycloak OIDC JWT token management
- **Database**: SQLite for local session/preference storage

---

## Product Requirements Document (PRD)

### 0) Purpose
The **Tourist Mobile Application** simulates a tourist's mobile device that:
- Provides an **interactive map interface** for location setting and tracking
- Offers **emergency SOS functionality** with one-click activation
- Supports **automated path simulation** for testing scenarios
- Authenticates via **Keycloak OIDC** and communicates through the Gateway
- Simulates **ESP32 device behavior** via MQTT for testing integration

### 1) Components & Architecture

| Component | Role | Port | Technology |
|---|---|---:|---|
| **Frontend** | Web UI (map + SOS + controls) | 2040 | HTML/CSS/JS + Leaflet |
| **Backend API** | Auth + Gateway proxy + MQTT bridge | 2040 | FastAPI |
| **Session Store** | Local preferences/state | - | SQLite |

**External Dependencies:**
- Gateway API: `http://<GATEWAY_IP>:2045`
- Gateway MQTT: `mqtt://<GATEWAY_IP>:2046`
- Keycloak: `https://<KEYCLOAK_IP>:2027`

### 2) Frontend Features

#### 2.1 Interactive Map
- **Technology**: Leaflet.js with OpenStreetMap tiles
- **Functionality**:
  - Click-to-set location (lat/lon display)
  - Current location marker with timestamp
  - Optional polyline path visualization
  - Zoom controls and basic map navigation

#### 2.2 SOS Controls
- **Giant SOS Toggle**: Large, prominent button with clear active/inactive states
- **Visual Feedback**: Color changes (red=active, green=inactive)
- **Confirmation**: Optional confirmation dialog for activation
- **Status Display**: Show SOS status and last sent timestamp

#### 2.3 Simulation Controls
- **Polyline Path**: 
  - Upload/define GPX or simple coordinate arrays
  - Auto-movement along path with configurable speed
  - Start/stop/pause controls
- **Manual Controls**:
  - Quick location presets (popular tourist areas)
  - Manual lat/lon input fields

#### 2.4 Status Dashboard
- **Connection Status**: Gateway connectivity indicator
- **Authentication**: Token status and refresh controls
- **Recent Activity**: Last sent locations and SOS events
- **Device Info**: Simulated device ID and registration status

### 3) Backend API Endpoints

#### 3.1 Web App Serving
```
GET /                    → Serve main web app
GET /static/*           → Static assets (CSS, JS, images)
```

#### 3.2 Authentication
```
GET /auth/login         → Redirect to Keycloak login
GET /auth/callback      → Handle OIDC callback
POST /auth/refresh      → Refresh JWT token
GET /auth/status        → Current auth status
```

#### 3.3 Location & SOS
```
POST /api/location      → Send location to Gateway
POST /api/sos           → Trigger SOS via Gateway
GET /api/status         → App status and connectivity
```

#### 3.4 Simulation Controls
```
POST /api/simulate/start → Start polyline simulation
POST /api/simulate/stop  → Stop simulation
GET /api/simulate/status → Current simulation state
```

#### 3.5 Device Registration
```
POST /api/device/register → Register simulated ESP32 device
GET /api/device/status    → Device registration status
```

### 4) Backend Implementation Details

#### 4.1 Gateway Integration
```python
# Location forwarding to Gateway
async def send_location(lat: float, lon: float, sos: bool = False):
    headers = {"Authorization": f"Bearer {jwt_token}"}
    payload = {
        "location": {"lat": lat, "lon": lon},
        "timestamp": datetime.utcnow().isoformat(),
        "sos": {"active": sos} if sos else None
    }
    response = await httpx.post(
        f"{GATEWAY_URL}/gw/ingest", 
        json=payload, 
        headers=headers
    )
    return response
```

#### 4.2 MQTT ESP32 Simulation
```python
# Simulate ESP32 MQTT messages
async def publish_esp32_sos(device_id: str, lat: float, lon: float):
    topic = f"esp32/{device_id}/sos"
    payload = {
        "ts": datetime.utcnow().isoformat(),
        "lat": lat,
        "lon": lon
    }
    mqtt_client.publish(topic, json.dumps(payload))
```

#### 4.3 Authentication Flow
- **Login**: Redirect to Keycloak → receive code → exchange for JWT
- **Storage**: Store JWT in session/local storage
- **Refresh**: Auto-refresh before expiration
- **Validation**: Verify token before Gateway calls

### 5) File Structure
```
/workspace/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── auth.py              # Keycloak OIDC handling
│   ├── gateway.py           # Gateway API client
│   ├── mqtt_client.py       # MQTT bridge for ESP32 simulation
│   ├── simulation.py        # Polyline path simulation
│   └── models.py            # Pydantic models
├── frontend/
│   ├── index.html           # Main web app
│   ├── static/
│   │   ├── app.js           # Frontend JavaScript
│   │   ├── map.js           # Leaflet map controls
│   │   ├── sos.js           # SOS functionality
│   │   └── style.css        # Styling
│   └── assets/
│       └── icons/           # SOS button icons
├── config/
│   ├── settings.py          # Configuration management
│   └── local.db             # SQLite database
└── requirements.txt         # Python dependencies
```

### 6) Configuration Management
```python
# Environment variables
GATEWAY_URL = "http://gateway:2045"
GATEWAY_MQTT_URL = "mqtt://gateway:2046"
KEYCLOAK_URL = "https://keycloak:2027"
KEYCLOAK_REALM = "mod-core"
KEYCLOAK_CLIENT_ID = "tourist-app"
DEVICE_ID = "tourist-sim-001"  # Simulated ESP32 ID
```

### 7) Development Workflow

#### 7.1 Container Startup
```bash
# Inside container
cd /workspace
python backend/main.py
# or
uvicorn backend.main:app --host 0.0.0.0 --port 2040 --reload
```

#### 7.2 Frontend Development
- Static files served by FastAPI
- Live reload for development
- Map testing with local coordinates

#### 7.3 Integration Testing
1. **Authentication**: Verify Keycloak login flow
2. **Gateway Communication**: Test location sending via `/gw/ingest`
3. **MQTT Integration**: Verify ESP32-style SOS messages
4. **SOS Flow**: End-to-end SOS from button to Police SEDI

### 8) Acceptance Criteria

**Core Functionality:**
- ✅ Web app loads with interactive map
- ✅ Click map to set location → location sent to Gateway
- ✅ SOS button → emergency alert sent via Gateway
- ✅ Keycloak authentication working
- ✅ Gateway connectivity status visible

**Advanced Features:**
- ✅ Polyline path simulation working
- ✅ ESP32 MQTT simulation functional
- ✅ Device registration successful
- ✅ Status dashboard showing real-time info

**Integration:**
- ✅ Gateway receives and forwards location data
- ✅ SOS alerts appear on Police SEDI system
- ✅ MQTT messages processed by Gateway Mosquitto
- ✅ Rate limiting respected (1/min average)

### 9) Performance & SLA Targets
- **Response Time**: Web app interactions < 200ms
- **Location Updates**: Send to Gateway within 500ms of map click
- **SOS Activation**: Alert sent within 1 second of button press
- **Simulation**: Polyline movement smooth at 1Hz update rate

### 10) Security Considerations
- **Token Handling**: Secure JWT storage and refresh
- **HTTPS**: All Gateway communication over HTTPS (except MQTT)
- **Input Validation**: Sanitize all location and user inputs
- **Rate Limiting**: Respect Gateway rate limits to prevent blocking

### 11) Authentication Notes
- OAuth2 tokens issued by Keycloak realm `mod-core`
- Quick token retrieval guide in `docs/Keycloak_Token_Guide.md`
- Demo credentials (dev only): `tourist-demo` / `tourist123`
- Use the retrieved `access_token` as Bearer for Gateway and MoD Core APIs

This implementation provides a complete tourist mobile application simulator that integrates with your Gateway infrastructure while offering both manual and automated testing capabilities.
