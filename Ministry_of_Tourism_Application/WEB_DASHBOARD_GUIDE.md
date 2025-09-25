# MoT Core - Real-Time Web Dashboard

## 🎯 Overview

The MoT Core Web Dashboard is a beautiful, real-time monitoring interface for tourist safety in India. It provides live tracking, red zone management, and emergency response capabilities with under 3-second refresh rates.

## 🚀 Quick Start

### Option 1: Using the Startup Script
```bash
./start_dashboard.sh
```

### Option 2: Manual Start
```bash
cd /workspace
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Dashboard URL:** http://localhost:8000

## 🌟 Key Features

### 1. **Real-Time Map Tracking**
- **Interactive Map**: Leaflet-powered map with multiple view modes (Standard, Satellite, Terrain, Dark)
- **Live Tourist Markers**: Color-coded markers showing tourist status:
  - 🟢 **Green**: Safe
  - 🟡 **Yellow**: Warning
  - 🔴 **Red**: Danger/Emergency
- **Automatic Refresh**: Updates every 2 seconds
- **Tourist Information**: Click markers to see detailed tourist info

### 2. **Red Zone Management**
- **Draw Red Zones**: Click "🎯 Draw Red Zone" to enter drawing mode
- **Multiple Shapes**: Support for polygons, rectangles, and circles
- **Real-Time Detection**: Automatically detects when tourists enter red zones
- **Visual Alerts**: Red zones are clearly marked on the map

### 3. **Tourist Lists & Monitoring**

#### All Tourists Online
- Complete list of active tourists
- Real-time status updates
- Safety scores (0-100%)
- Last seen timestamps
- Quick action buttons

#### Red Zone Alerts
- Tourists currently in red zones
- Automatic alerts when tourists enter restricted areas
- Immediate visual and banner notifications

#### Critical Alerts
- SOS signals
- Emergency situations
- Safety breaches
- High-priority incidents

### 4. **Police Action & E-FIR System**
- **Instant Response**: Click "🚔 Police Action" next to any tourist
- **E-FIR Generation**: Automatic Electronic First Information Report creation
- **Incident Classification**:
  - Red Zone Entry
  - SOS Alert
  - Safety Breach
  - Emergency
- **Priority Levels**: High Priority, Critical, Emergency
- **Real-Time Forwarding**: Immediate notification to police systems

## 🎨 User Interface

### Header Dashboard
- **Ministry of Tourism** branding
- **Live Statistics**:
  - Total Tourists Online
  - Tourists in Red Zones
  - Active Alerts
- **Real-time counters** update automatically

### Map Controls
- **Style Selector**: Switch between map views
- **Red Zone Mode**: Toggle drawing tools
- **Layer Controls**: Manage map overlays
- **Scale Indicator**: Distance reference

### Side Panels
- **Responsive Design**: Adapts to screen size
- **Scrollable Lists**: Handle large numbers of tourists
- **Status Indicators**: Color-coded for quick reference
- **Action Buttons**: One-click operations

## 🔄 Real-Time Features

### WebSocket Connection
- **Live Updates**: Instant notifications via WebSocket
- **Auto-Reconnect**: Handles connection drops gracefully
- **Broadcast System**: Multi-client support

### Data Refresh
- **Tourist Locations**: Every 2 seconds
- **Alert Status**: Every 2 seconds
- **WebSocket Events**: Instant (< 1 second)

### Update Types
- Tourist location changes
- New alerts
- Red zone entries
- E-FIR submissions
- Status changes

## 🚨 Alert System

### Visual Alerts
- **Banner Notifications**: Top-of-screen alerts
- **Color Coding**: Immediate visual status
- **Pulsing Animations**: Critical alerts
- **Sound Notifications**: Can be enabled

### Alert Triggers
- Tourist enters red zone
- SOS button pressed
- Safety score drops below threshold
- Communication lost with device
- Emergency beacon activated

## 🔧 API Endpoints

### Dashboard APIs
```
GET  /api/v1/tourists/live    - Live tourist data
GET  /api/v1/alerts/active    - Active alerts
POST /api/v1/police/efir      - Create E-FIR
POST /api/v1/admin/red-zones  - Create red zone
```

### WebSocket
```
WS   /ws/realtime             - Real-time updates
```

### Static Files
```
GET  /                        - Main dashboard
GET  /static/*                - Dashboard assets
```

## 🎯 Usage Scenarios

### 1. **Normal Monitoring**
1. Open dashboard at http://localhost:8000
2. View all tourists on the map
3. Monitor safety scores and statuses
4. Track location updates in real-time

### 2. **Red Zone Management**
1. Click "🎯 Draw Red Zone" button
2. Select drawing tool (polygon/rectangle/circle)
3. Draw the restricted area on the map
4. System automatically monitors entries

### 3. **Emergency Response**
1. Receive critical alert notification
2. Click tourist name in alert list
3. Click "🚔 Police Action" button
4. Fill incident details
5. Submit E-FIR to police system

### 4. **Tourist Status Check**
1. Find tourist in "All Tourists" list
2. Check safety score and status
3. View last known location
4. Click map marker for detailed popup

## 🎨 Map Features

### Base Layers
- **Standard**: OpenStreetMap roads and features
- **Satellite**: High-resolution satellite imagery
- **Terrain**: Topographic with elevation data
- **Dark Mode**: Dark theme for night operations

### Overlays
- **Tourist Markers**: Real-time positions
- **Red Zones**: Restricted areas
- **Scale Control**: Distance measurements
- **Layer Control**: Toggle overlays

### Interactive Elements
- **Zoom Controls**: Mouse wheel, buttons
- **Pan**: Click and drag
- **Popup Windows**: Click markers for details
- **Drawing Tools**: Create red zones
- **Tooltip**: Hover for quick info

## 📱 Responsive Design

### Desktop (1920x1080+)
- Full three-column layout
- Large map with detailed controls
- Complete side panels
- All features visible

### Tablet (768-1024px)
- Two-column layout
- Collapsible panels
- Touch-friendly controls
- Optimized map size

### Mobile (< 768px)
- Single-column stacked layout
- Swipeable panels
- Large touch targets
- Simplified interface

## 🔒 Security Features

### Authentication
- Built on mTLS certificate verification
- OIDC integration with Keycloak
- Session management
- Role-based access control

### Data Protection
- Encrypted WebSocket connections
- Secure API endpoints
- Request validation
- Rate limiting

## 🎛️ Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
WEBSOCKET_ENABLED=true
REFRESH_INTERVAL=2000  # milliseconds
```

### Map Settings
```javascript
const mapConfig = {
    center: [20.5937, 78.9629],  // India center
    zoom: 5,
    maxZoom: 20,
    refreshRate: 2000  // 2 seconds
};
```

## 🔍 Troubleshooting

### Dashboard Won't Load
1. Check server is running: `curl http://localhost:8000/health`
2. Verify port 8000 is available
3. Check browser console for errors
4. Ensure `/workspace/web/index.html` exists

### Real-Time Updates Not Working
1. Check WebSocket connection in browser dev tools
2. Verify network allows WebSocket connections
3. Check server logs for WebSocket errors
4. Test with different browser

### Map Not Displaying
1. Check internet connection (requires CDN access)
2. Verify Leaflet CDN is accessible
3. Check browser console for JavaScript errors
4. Try different map style

### API Errors
1. Check server logs: `tail -f logs/mod-core.log`
2. Verify database connection
3. Check API endpoint URLs
4. Test with curl commands

## 🚀 Production Deployment

### Performance Optimization
- Enable map tile caching
- Use WebSocket connection pooling
- Implement data pagination
- Add response compression

### Monitoring
- Real-time performance metrics
- WebSocket connection monitoring
- API response time tracking
- Error rate monitoring

### Scaling
- Load balancer for multiple instances
- Redis for session management
- Database read replicas
- CDN for static assets

## 📈 Analytics & Metrics

### Built-in Metrics
- Tourist count over time
- Red zone violations
- Response times
- Alert frequency
- Geographic distribution

### Custom Dashboards
- Grafana integration
- Prometheus metrics
- Custom KPI tracking
- Historical analysis

## 🎉 Success! Your Complete MoT Core Dashboard

You now have a fully functional, beautiful real-time tourist safety monitoring system with:

✅ **Real-time map tracking** (< 3s refresh)  
✅ **Interactive red zone drawing**  
✅ **Tourist lists with live status**  
✅ **Police action buttons**  
✅ **E-FIR generation system**  
✅ **WebSocket real-time updates**  
✅ **Critical alerts monitoring**  
✅ **Beautiful responsive UI**  
✅ **Multi-map view modes**  
✅ **Professional MoT branding**  

**🌐 Access your dashboard at: http://localhost:8000**

---

*Built for the Ministry of Tourism, Government of India*  
*Ensuring tourist safety through technology* 🇮🇳
