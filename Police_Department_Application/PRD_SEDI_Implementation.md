# Police SEDI Application - Implementation PRD
**Version:** 1.0  
**Date:** September 25, 2025  
**Environment:** Single Container Deployment (Ubuntu 22.04)

## 1. Executive Summary

The Police SEDI (Security & Emergency Data Interface) application is a real-time incident monitoring system that consumes live data streams from the Ministry of Defense (MoD) Core system. This PRD defines the implementation strategy for a single-container deployment running on Ubuntu 22.04 with Python 3.10, Node.js 12.22.9, and PostgreSQL 14.19.

### 1.1 Key Objectives
- Provide real-time incident monitoring for police operations
- Display live incidents on an interactive map interface
- Enable police officers to acknowledge and respond to incidents
- Maintain minimal local data storage for performance and compliance
- Ensure secure communication with MoD Core via mTLS and OIDC

## 2. Technical Architecture

### 2.1 Container Environment
**Base:** Ubuntu 22.04 (already running)  
**Available Tools:**
- Python 3.10.12
- Node.js v12.22.9  
- PostgreSQL 14.19
- Build tools, curl, wget, openssl

### 2.2 System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Police SEDI Container                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Frontend      │  │   Backend       │  │ PostgreSQL  │ │
│  │   (React SPA)   │  │   (FastAPI)     │  │   (Local)   │ │
│  │   Static Files  │◄─┤   Port 2035     │◄─┤  Port 2036  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│           │                     │                          │
│           │                     │                          │
│           ▼                     ▼                          │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │   Keycloak      │  │   MoD Core      │                 │
│  │   (External)    │  │   Port 2025     │                 │
│  │   OIDC Auth     │  │   SSE Stream    │                 │
│  └─────────────────┘  └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Port Allocation
- **2035**: FastAPI application (HTTPS) serving both API and static frontend
- **2036**: PostgreSQL database (local connection only)
- **External**: MoD Core (2025), Keycloak (external OIDC provider)

## 3. Component Specifications

### 3.1 Backend (FastAPI)
**Location:** `/workspace/backend/`  
**Framework:** FastAPI 0.104.1  
**Features:**
- RESTful API for incident management
- Server-Sent Events (SSE) for real-time updates
- OIDC authentication with Keycloak
- mTLS client for MoD Core communication
- Static file serving for React frontend

**Key Modules:**
```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── auth/
│   ├── oidc.py         # OIDC authentication
│   └── middleware.py   # Auth middleware
├── services/
│   ├── mod_client.py   # MoD Core integration
│   ├── incident_service.py
│   └── sse_service.py  # Real-time streaming
├── models/
│   ├── database.py     # SQLAlchemy models
│   └── schemas.py      # Pydantic schemas
└── api/
    ├── incidents.py    # Incident endpoints
    ├── auth.py         # Authentication endpoints
    └── health.py       # Health check endpoints
```

### 3.2 Frontend (React SPA)
**Location:** `/workspace/frontend/`  
**Framework:** React 18 with TypeScript  
**Build Tool:** Vite (for development, static build for production)

**Key Components:**
```
frontend/src/
├── components/
│   ├── Dashboard.tsx       # Main dashboard layout
│   ├── IncidentList.tsx   # Real-time incident list
│   ├── MapView.tsx        # Leaflet map component
│   ├── IncidentDetails.tsx
│   └── AuthCallback.tsx   # OIDC callback handler
├── services/
│   ├── api.ts             # API client
│   ├── sse.ts             # SSE connection management
│   └── auth.ts            # Authentication service
├── store/
│   ├── incidents.ts       # Incident state management
│   └── auth.ts            # Authentication state
└── types/
    └── incident.ts        # TypeScript definitions
```

### 3.3 Database (PostgreSQL)
**Version:** PostgreSQL 14.19  
**Port:** 2036  
**Storage:** Local container filesystem

**Schema:**
```sql
-- Core tables (minimal data retention)
incidents (alert_id, tourist_id, type, created_at, last_status, location, score_band)
actions (id, alert_id, officer_id, action, performed_at, note)
settings (key, value, updated_at)
```

## 4. API Specifications

### 4.1 Authentication Endpoints
```
GET  /auth/login          # Initiate OIDC login
GET  /auth/callback       # OIDC callback handler
POST /auth/logout         # Logout and cleanup
GET  /auth/user           # Get current user info
```

### 4.2 Incident Management
```
GET  /api/v1/incidents                    # List incidents (with filters)
GET  /api/v1/incidents/{alert_id}         # Get specific incident
POST /api/v1/incidents/{alert_id}/ack     # Acknowledge incident
GET  /api/v1/incidents/stats              # Dashboard statistics
```

### 4.3 Real-time Streaming
```
GET  /api/v1/stream       # SSE endpoint for real-time updates
```

### 4.4 System Endpoints
```
GET  /health              # Health check
GET  /metrics             # Basic metrics
GET  /                    # Serve React SPA
```

## 5. Data Models

### 5.1 Incident Model
```typescript
interface Incident {
  alert_id: number;
  tourist_id: string;        // Pseudonymous ID
  type: 'SOS' | 'RED_ZONE' | 'DISCONNECTION';
  created_at: string;        // ISO timestamp
  last_status: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';
  last_update_at: string;
  location?: {
    lat: number;
    lng: number;
    accuracy: number;
  };
  score_band?: 'HIGH' | 'MEDIUM' | 'LOW';
  details?: string;
}
```

### 5.2 ACK Request Model
```typescript
interface AckRequest {
  alert_id: number;
  tourist_id: string;
  note: string;
  officer_id: string;
}
```

## 6. Security Requirements

### 6.1 Authentication Flow
1. User accesses SEDI frontend → redirected to Keycloak
2. Keycloak validates credentials → returns OIDC token with `POLICE` role
3. Frontend stores JWT token → includes in all API requests
4. Backend validates JWT → extracts officer information
5. Backend uses client certificate for MoD Core mTLS communication

### 6.2 Certificate Management
**Location:** `/workspace/certs/` (mounted read-only)
- `sedi.crt` - Client certificate for mTLS with MoD Core
- `sedi.key` - Private key for client certificate
- `ca.crt` - Certificate Authority for MoD Core validation

### 6.3 Security Headers
- HTTPS enforcement (port 2035)
- CORS configuration for same-origin
- Content Security Policy (CSP)
- X-Frame-Options, X-Content-Type-Options

## 7. Integration Specifications

### 7.1 MoD Core Stream Consumption
**Endpoint:** `GET https://<MoD_IP>:2025/v1/police/stream`  
**Authentication:** OIDC (POLICE role) + mTLS client certificate  
**Protocol:** Server-Sent Events (SSE)  
**Frequency:** Snapshot every 5 seconds + real-time events

**Stream Data Format:**
```json
{
  "type": "incident_update",
  "data": {
    "alert_id": 987654,
    "tourist_id": "b1d0b691-...-9a",
    "type": "SOS",
    "created_at": "2025-09-25T10:30:00Z",
    "status": "ACTIVE",
    "location": { "lat": 40.7128, "lng": -74.0060, "accuracy": 10 },
    "score_band": "HIGH"
  }
}
```

### 7.2 MoD Core ACK Posting
**Endpoint:** `POST https://<MoD_IP>:2025/v1/police/ack`  
**Authentication:** OIDC (POLICE role) + mTLS client certificate

## 8. User Experience Requirements

### 8.1 Dashboard Layout
- **Header:** Police SEDI logo, user info, logout button
- **Sidebar:** Filters (incident type, time range, status)
- **Main Area:** Split view - incident list (left) + map (right)
- **Details Panel:** Expandable drawer for incident details

### 8.2 Incident List Features
- Real-time updates via SSE
- Color-coded by incident type and urgency
- Sortable columns (time, type, status, location)
- Filter by type, time range, status
- ACK button for active incidents

### 8.3 Map Component
- OpenStreetMap base layer
- Red polygon markers for incident locations
- 10x10 meter zoom capability
- Click to select incident
- Real-time position updates

### 8.4 Responsive Design
- Desktop-first design (police workstations)
- Minimum resolution: 1024x768
- Support for up to 200 concurrent incidents

## 9. Performance Requirements

### 9.1 Response Times (SLOs)
- **New Incident Rendering:** ≤ 2 seconds (p95)
- **SSE Reconnection:** ≤ 3 seconds after connection loss
- **API Response Time:** ≤ 500ms for incident operations
- **Map Rendering:** ≤ 1 second for initial load

### 9.2 Scalability
- Support up to 200 concurrent incidents
- Handle 50+ simultaneous police users
- Database queries optimized for real-time performance

## 10. Deployment Strategy

### 10.1 Single Container Setup
```bash
# 1. Setup PostgreSQL (local service)
service postgresql start
sudo -u postgres createdb sedi_db
sudo -u postgres createuser sedi_user

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Build React frontend (if using build process)
cd frontend && npm install && npm run build

# 4. Start FastAPI application
uvicorn backend.main:app --host 0.0.0.0 --port 2035 \
  --ssl-keyfile certs/sedi.key --ssl-certfile certs/sedi.crt
```

### 10.2 Environment Configuration
```bash
# Database
DATABASE_URL=postgresql+asyncpg://sedi_user:password@localhost:2036/sedi_db

# MoD Core
MOD_CORE_URL=https://<MoD_IP>:2025
MOD_CLIENT_CERT_PATH=/workspace/certs/sedi.crt
MOD_CLIENT_KEY_PATH=/workspace/certs/sedi.key

# OIDC
OIDC_ISSUER_URL=https://keycloak.police.gov/auth/realms/police
OIDC_CLIENT_ID=sedi-police-app
```

## 11. Implementation Phases

### Phase 1: Foundation (Days 1-2)
- [ ] Project structure setup
- [ ] PostgreSQL local configuration
- [ ] Basic FastAPI application
- [ ] Database models and migrations

### Phase 2: Core Backend (Days 3-4)
- [ ] OIDC authentication implementation
- [ ] MoD Core client with mTLS
- [ ] Incident API endpoints
- [ ] SSE streaming service

### Phase 3: Frontend Development (Days 5-6)
- [ ] React application setup
- [ ] Authentication flow
- [ ] Incident list component
- [ ] Map integration with Leaflet

### Phase 4: Integration & Testing (Days 7-8)
- [ ] Real-time SSE integration
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Security validation

## 12. Acceptance Criteria

### 12.1 Functional Requirements
- [ ] Successfully authenticate with Keycloak using POLICE role
- [ ] Establish SSE connection to MoD Core
- [ ] Display real-time incident updates within 2 seconds
- [ ] Render incidents on interactive map with 10x10m precision
- [ ] Send ACK to MoD Core and receive confirmation
- [ ] Auto-reconnect SSE within 3 seconds after disconnection

### 12.2 Technical Requirements
- [ ] HTTPS on port 2035 with valid certificates
- [ ] PostgreSQL running on port 2036
- [ ] All components running in single container
- [ ] Minimal memory footprint (< 2GB total)
- [ ] Zero external dependencies beyond MoD Core and Keycloak

## 13. Monitoring & Logging

### 13.1 Health Checks
- Database connectivity
- MoD Core stream status
- Certificate validity
- Memory and CPU usage

### 13.2 Audit Logging
- All ACK actions with officer ID and timestamp
- Authentication events
- Failed connection attempts
- System errors and warnings

---

**Next Steps:** This PRD serves as the foundation for implementation. The development will proceed component by component, starting with the basic FastAPI setup and PostgreSQL configuration.
