# MoD Core Implementation PRD - Single Container Multi-Process Architecture

## Executive Summary

The Ministry of Tourism Core Safety Backend (MoD Core) is implemented as a single-container, multi-process system that manages tourist safety through real-time telemetry processing, geofencing, and police coordination. This PRD outlines the complete implementation strategy for deploying all required services within the existing Ubuntu 22.04 container.

## 1. Architecture Overview

### 1.1 Single Container Process Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Ubuntu 22.04 Container                   │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ mod-proxy   │  │   mod-api   │  │  keycloak   │         │
│  │ (Nginx)     │  │ (FastAPI)   │  │ (Java)      │         │
│  │ Port 2025   │  │ Port 8000   │  │ Port 2027   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   mod-db    │  │ prometheus  │  │   grafana   │         │
│  │(PostgreSQL) │  │ (Go binary) │  │ (Go binary) │         │
│  │ Port 2026   │  │ Port 2028   │  │ Port 2029   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │eth-adapter  │  │  notifier   │                          │
│  │ (Python)    │  │ (Python)    │                          │
│  │ Internal    │  │ Internal    │                          │
│  └─────────────┘  └─────────────┘                          │
│                                                             │
│           Managed by Supervisor                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Service Components

| Component | Purpose | Port | Process Manager |
|-----------|---------|------|-----------------|
| mod-proxy | mTLS termination & reverse proxy | 2025 | Supervisor |
| mod-api | FastAPI core application | 8000 (internal) | Supervisor |
| mod-db | PostgreSQL + PostGIS database | 2026 | Supervisor |
| keycloak | OIDC identity provider | 2027 | Supervisor |
| prometheus | Metrics collection | 2028 | Supervisor |
| grafana | Monitoring dashboards | 2029 | Supervisor |
| eth-adapter | Ethereum testnet client | Internal | Supervisor |
| notifier | Local messaging service | Internal | Supervisor |

## 2. API Specifications

### 2.1 Tourist Mobile API

#### POST /v1/app/ingest
**Purpose**: Process tourist telemetry and return contextual safety data

**Authentication**: OIDC Bearer token (TOURIST role)
**Rate Limiting**: 1 request/minute average, burst allowance for SOS
**Idempotency**: 24-hour deduplication via `Idempotency-Key` header

**Request Schema**:
```json
{
  "tourist_id": "uuid",
  "device_id": "uuid", 
  "position": {
    "lat": "float",
    "lon": "float", 
    "alt": "float",
    "speed_mps": "float",
    "ts": "ISO8601"
  },
  "health": {
    "heart_rate": "int",
    "fall_detected": "boolean",
    "battery": "float"
  },
  "sos": {
    "active": "boolean"
  },
  "app": {
    "build": "string",
    "platform": "string"
  }
}
```

**Response Schema**:
```json
{
  "ack": "boolean",
  "safety": {
    "score": "int (0-100)",
    "red_zone_distance_m": "float",
    "in_red_zone": "boolean"
  },
  "advisories": ["string"],
  "open_alert": "object|null"
}
```

#### GET /v1/app/fences/summary
**Purpose**: Quick nearest red-zone distance + in/out flag
**Parameters**: `lat`, `lon`
**Authentication**: OIDC (TOURIST)

#### GET /v1/app/messages
**Purpose**: Server-side localized advisories for tourists
**Authentication**: OIDC (TOURIST)
**Localization**: English only in MVP

### 2.2 Police Streaming API

#### GET /v1/police/stream (SSE)
**Purpose**: Real-time operational feed for police dispatch
**Authentication**: OIDC + mTLS client certificate
**Frequency**: 5-second snapshots + immediate event push
**SLA**: Event lag ≤ 3 seconds (p95)

**Event Schema**:
```json
{
  "snapshot_ts": "ISO8601",
  "totals": {
    "tourists_monitored": "int",
    "active_alerts": {
      "sos": "int",
      "geofence": "int", 
      "inactivity": "int",
      "deviation": "int",
      "vitals": "int"
    }
  },
  "tourists": [{
    "tourist_id": "uuid",
    "position": {
      "lat": "float",
      "lon": "float",
      "ts": "ISO8601"
    },
    "score": "int",
    "status_flags": ["string"],
    "last_alert": {
      "alert_id": "int",
      "type": "string",
      "ts": "ISO8601"
    }
  }]
}
```

#### POST /v1/police/ack
**Purpose**: Police acknowledgement for alerts
**Authentication**: OIDC (POLICE) + mTLS

```json
{
  "alert_id": "int",
  "tourist_id": "uuid",
  "note": "string",
  "officer_id": "string"
}
```

## 3. Security Implementation

### 3.1 Certificate Management
- Self-signed root CA for internal PKI
- Server certificate for mod-proxy (mTLS termination)
- Client certificates for Police SEDI and User Gateway
- All certificates stored in `/workspace/certs/`

### 3.2 Authentication & Authorization
- **Keycloak Realm**: `mod-core`
- **Clients**: 
  - `tourist-app` (public, PKCE)
  - `police-sedi` (confidential, client-credentials)
  - `mod-admin` (confidential, authorization-code)

### 3.3 Role-Based Access Control
```json
{
  "TOURIST": [
    "app:ingest",
    "app:fences:read", 
    "app:messages:read"
  ],
  "POLICE": [
    "police:stream:read",
    "police:ack:write"
  ],
  "ADMIN": [
    "admin:geofences:write",
    "admin:analytics:read"
  ]
}
```

## 4. Database Schema

### 4.1 Core Tables
```sql
-- Tourists
CREATE TABLE tourists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    digital_id_hash VARCHAR(64) UNIQUE,
    id_expiry TIMESTAMPTZ,
    emergency_contact JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Digital ID verification
CREATE TABLE digital_ids (
    tourist_id UUID REFERENCES tourists(id),
    offchain_hash VARCHAR(64),
    eth_tx_hash VARCHAR(66),
    chain VARCHAR(20) DEFAULT 'sepolia',
    verified_at TIMESTAMPTZ
);

-- Devices
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tourist_id UUID REFERENCES tourists(id),
    hw_id VARCHAR(255) UNIQUE,
    device_type VARCHAR(50),
    last_seen TIMESTAMPTZ
);

-- Geofences with PostGIS
CREATE TABLE geofences (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    severity INTEGER CHECK (severity BETWEEN 1 AND 10),
    geom GEOMETRY(Polygon, 4326),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Location tracking
CREATE TABLE locations (
    id BIGSERIAL PRIMARY KEY,
    tourist_id UUID REFERENCES tourists(id),
    device_id UUID REFERENCES devices(id),
    recorded_at TIMESTAMPTZ,
    geom GEOMETRY(Point, 4326),
    speed_mps FLOAT,
    altitude FLOAT,
    metadata JSONB
);

-- Alert lifecycle
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    tourist_id UUID REFERENCES tourists(id),
    alert_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'NEW',
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ack_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ
);

-- Audit trail
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor VARCHAR(255),
    action VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id VARCHAR(255),
    performed_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);
```

## 5. Business Logic Implementation

### 5.1 Safety Scoring Algorithm
```python
def calculate_safety_score(tourist_data: dict) -> int:
    base_score = 100
    
    # Geofence penalties
    if tourist_data.get('in_red_zone'):
        base_score -= 40
    
    # Distance-based reduction
    red_zone_distance = tourist_data.get('red_zone_distance_m', float('inf'))
    if red_zone_distance < 500:
        base_score -= max(0, 30 - (red_zone_distance / 500 * 30))
    
    # Health indicators
    heart_rate = tourist_data.get('health', {}).get('heart_rate', 70)
    if heart_rate > 100 or heart_rate < 50:
        base_score -= 10
    
    # Battery level
    battery = tourist_data.get('health', {}).get('battery', 1.0)
    if battery < 0.2:
        base_score -= 15
    
    # SOS active
    if tourist_data.get('sos', {}).get('active'):
        base_score = 0
    
    return max(0, min(100, base_score))
```

### 5.2 Alert Generation Rules
- **SOS Detection**: Immediate CRITICAL alert
- **Geofence Breach**: HIGH priority for red zones
- **Inactivity Detection**: MEDIUM priority for prolonged silence
- **Health Vitals**: MEDIUM priority for anomalous readings

## 6. Performance Requirements

### 6.1 Service Level Objectives (SLOs)
- **API Response Time**: p95 ≤ 800ms for `/v1/app/ingest`
- **Alert Latency**: SOS → Police notification ≤ 2 seconds (p95)
- **Stream Lag**: Police SSE events ≤ 3 seconds (p95)
- **Availability**: ≥ 99.9% uptime
- **Error Rate**: ≤ 0.5% for critical endpoints

### 6.2 Scalability Targets
- **Concurrent Users**: 1,000 active tourists
- **Request Rate**: 1,000 requests/minute sustained
- **Database**: 1M location records/day retention
- **Storage**: 30-day data retention policy

## 7. Monitoring & Observability

### 7.1 Key Metrics
- **Business Metrics**: tourists_total, active_alerts_by_type, sos_incidents_24h
- **Technical Metrics**: api_request_duration_seconds, database_connections_active
- **Infrastructure Metrics**: container_cpu_usage, container_memory_usage

### 7.2 Grafana Dashboards
- Devices below recommended battery
- Devices near red zones
- Total alerts by type
- SOS incidents in past hour
- Open cases and response times

## 8. Implementation Phases

### Phase 1: Infrastructure Setup (Days 1-2)
- Install all service dependencies
- Configure supervisor for process management
- Setup SSL certificates and mTLS

### Phase 2: Database & Core API (Days 2-4)
- PostgreSQL + PostGIS setup
- FastAPI application structure
- Basic authentication middleware

### Phase 3: Business Logic (Days 4-6)
- Safety scoring engine
- Geofencing service
- Alert generation system

### Phase 4: Police Integration (Days 6-7)
- SSE streaming implementation
- Real-time notifications
- ACK endpoint

### Phase 5: Monitoring & Testing (Days 7-8)
- Prometheus metrics setup
- Grafana dashboards
- End-to-end testing

## 9. Acceptance Criteria

### 9.1 Functional Requirements
- ✅ Tourist telemetry ingestion with safety scoring
- ✅ Real-time geofence breach detection
- ✅ Police SSE stream with <3s latency
- ✅ Alert acknowledgment system
- ✅ Ethereum testnet integration

### 9.2 Non-Functional Requirements
- ✅ mTLS + OIDC authentication
- ✅ 99.9% availability
- ✅ Sub-800ms API response times
- ✅ Comprehensive monitoring
- ✅ Audit trail for all operations

## 10. Risk Mitigation

### 10.1 Technical Risks
- **Single Point of Failure**: Supervisor monitoring and auto-restart
- **Performance Bottlenecks**: Database connection pooling and caching
- **Security Vulnerabilities**: Regular security audits and updates

### 10.2 Operational Risks
- **Certificate Expiry**: Automated renewal scripts
- **Service Dependencies**: Health check endpoints for all services
- **Data Loss**: Regular database backups and WAL archiving

---

This PRD provides comprehensive guidance for implementing the MoD Core system as a single-container, multi-process architecture while meeting all specified requirements and maintaining operational excellence.
