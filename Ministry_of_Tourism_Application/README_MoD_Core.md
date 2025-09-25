# Ministry of Tourism Core Safety Backend (MoD Core) — PRD (MVP)

## 0) Purpose & Scope
The **MoD Core** is the authoritative backend that:
- Receives **tourist telemetry** (GPS, health, SOS) and returns **contextual safety** (nearest red-zone distance, advisories, safety score).
- Publishes a **minimal, response-oriented stream** to **Police SEDI** (only: SOS, irregular disconnections without prior notify, confirmed red-zone presence without user confirmation).
- Maintains **geofences**, **rules/scoring**, **alerts/incident lifecycle**, **digital ID verification (Ethereum testnet hash/pointer)**, and **auditing**.
- Enforces **encrypted transport (mTLS)** and **OIDC (Keycloak)** for all external clients.

**Constraints**
- Single host, **multi-container** (Docker). No DNS; call by IP.
- **Port range allowed: 2025–2050** (all services must map within this range).
- Language/runtime: **Python (FastAPI)** for API; Postgres + PostGIS for geo.
- Separate DBMS instances: **MoD DB ≠ Police DB**.
- No external push/SMS providers: use **local messaging** only (pull via API).

---

## 1) Components & Ports (host → container)

| Component   | Role                                              | Port map | Notes |
|---|---|---:|---|
| `mod-proxy` | Reverse proxy + **mTLS** termination (HTTPS/SSE)  | **2025:443** | Self-signed root CA; requires client cert from Police SEDI & User Gateway |
| `mod-api`   | FastAPI core (MoD external/internal APIs)         | (behind proxy) | Only reachable via `mod-proxy` |
| `mod-db`    | PostgreSQL + PostGIS (MoD data)                   | **2026:5432** | Volume-backed; encryption at rest recommended |
| `keycloak`  | OIDC provider (tourist + officers)                | **2027:8443** | Self-signed TLS; local realm/clients |
| `prometheus`| Metrics scrape                                    | **2028:9090** | Internal |
| `grafana`   | Dashboards                                        | **2029:3000** | Internal |
| `eth-adapter` | Ethereum testnet client/adapter                 | (internal) | Uses provider key (Sepolia/Holesky) |
| `notifier`  | Local messaging aggregator                        | (internal) | For advisories/messages pull API |

> External callers (Police SEDI, User Gateway, Tourist App via Gateway) only hit **`https://<HOST_IP>:2025`** (mTLS + OIDC).

---

## 2) Security Model
- **Identity**: Keycloak realms/clients  
  - `tourist-app` (public) → tokens for mobile/gateway.  
  - `police-sedi` (confidential) → client-credentials for SSE & ACK.  
  - `mod-admin` (confidential) → internal ops.
- **mTLS** on `mod-proxy` (port 2025):  
  - Self-signed **root CA**; issue **server cert** to MoD proxy and **client certs** to Police SEDI & User Gateway.  
  - Verify **client cert + OIDC token** on every external call.
- **Authorization** (role gates):  
  - `TOURIST` → App ingest + fences summary + messages.  
  - `POLICE` → Stream + ACK (no bulk pulls, no PII).  
  - `TOURISM`/`ADMIN` → analytics, geofence admin (internal).
- **Data minimization to Police**: only response-essential fields (no full profiles/PII).

---

## 3) External API (MoD Core)

**Base URL**: `https://<HOST_IP>:2025` (mTLS + OIDC required)

### 3.1 Tourist Mobile API (via Gateway in MVP)

#### `POST /v1/app/ingest`
Upsert tourist telemetry and return contextual safety.

Auth: OIDC (`TOURIST`)  
Idempotency: `Idempotency-Key` header (dedup within 24h)  
Rate guidance: avg **1/min** per tourist; bursts allowed on SOS

**Request**
```json
{
  "tourist_id": "b1d0b691-...-9a",
  "device_id": "9ce2-...-11",
  "position": {"lat": 26.162, "lon": 91.779, "alt": 53.4, "speed_mps": 0.0, "ts": "2025-09-24T14:30:30Z"},
  "health": {"heart_rate": 82, "fall_detected": false, "battery": 0.65},
  "sos": {"active": false},
  "app": {"build": "1.0.0", "platform": "android"},
  "idempotency_key": "6e54d8e8-2a..."
}
```

**Response**
```json
{
  "ack": true,
  "safety": {
    "score": 88,
    "red_zone_distance_m": 142.7,
    "in_red_zone": false
  },
  "advisories": ["Stay on lit roads after dusk."],
  "open_alert": null
}
```

#### `GET /v1/app/fences/summary?lat=<>&lon=<>`
Quick nearest red-zone distance + in/out flag.

Auth: OIDC (`TOURIST`)

#### `GET /v1/app/messages`
Server-side localized advisories for the tourist.

Auth: OIDC (`TOURIST`)  
Localization: **English only in MVP** (infra supports i18n later).

---

### 3.2 Police Stream & ACK

#### `GET /v1/police/stream`  (SSE)
Response-oriented operational feed.

Auth: OIDC (`POLICE`) **and** client cert (mTLS)  
Cadence: **snapshot every 5 s** + change events; target event lag ≤ **3 s** (p95)

**Event payload**
```json
{
  "snapshot_ts": "2025-09-24T14:32:00Z",
  "totals": {
    "tourists_monitored": 412,
    "active_alerts": {"sos": 2, "geofence": 1, "inactivity": 0, "deviation": 0, "vitals": 0}
  },
  "tourists": [
    {
      "tourist_id": "b1d0b691-...-9a",
      "position": {"lat": 26.162, "lon": 91.779, "ts": "2025-09-24T14:31:50Z"},
      "score": 42,
      "status_flags": ["sos"],
      "last_alert": {"alert_id": 987654, "type": "SOS", "ts": "2025-09-24T14:31:52Z"}
    }
  ]
}
```

#### `POST /v1/police/ack`
Police “OK/responding” acknowledgement for an alert.

Auth: OIDC (`POLICE`) + mTLS  
Body:
```json
{
  "alert_id": 987654,
  "tourist_id": "b1d0b691-...-9a",
  "note": "Unit dispatched",
  "officer_id": "ps-12-ajay"
}
```
Response:
```json
{"status":"ACK","at":"2025-09-24T14:33:03Z"}
```

---

## 4) Rules, Alerts & Scoring
- **Geofence breach**: inside polygon with severity ≥ threshold → `GEOFENCE`.
- **Irregular disconnection** (no update ≥ X minutes in daytime) without prior user pause/notify → `INACTIVITY` (police-visible).
- **Red-zone without confirmation**: user didn’t respond to “Are you safe?” within Y minutes while in red zone → escalate to police.
- **SOS** explicit → `SOS`.
- **Vitals**: HR out-of-range or fall detection → `VITALS`.
- **Safety score**: base 100 − penalties; clamp [0..100].

All alerts have lifecycle: `NEW → ACK → RESOLVED`. Police sees only response-worthy alerts.

---

## 5) Data Model (high level)
- `tourists (uuid, digital_id_hash, id_expiry, emergency_contact, ...)`
- `digital_ids (tourist_id, offchain_hash, eth_tx_hash, chain)`
- `devices (uuid, tourist_id, hw_id, type)`
- `geofences (id, name, severity, geom: polygon, active)`
- `locations (id, tourist_id, device_id, at, geom: point, speed, alt)`
- `alerts (id, tourist_id, type, status, payload, created_at, ack_at, resolve_at)`
- `consents (tourist_id, live_share, retention_days)`
- `audit_logs (id, actor, action, entity, at, meta)`

**Retention (default)**: trip end + **30 days** (configurable).  
**PII on-chain**: **none** (store only hashes/pointers; verification via Ethereum testnet).

---

## 6) Ethereum Testnet Integration
- On digital ID issuance: compute off-chain profile hash → **submit tx** to Sepolia/Holesky.  
- Store `eth_tx_hash`; expose internal **verify** routine comparing presented proof with chain hash.

---

## 7) Observability (Prometheus + Grafana)
**Metrics (examples)**  
- `tourists_total`  
- `active_alerts{type}`  
- `sos_latency_ms`  
- `ingest_rate_total`  
- `stream_clients`  
- `geofence_hits_total`  
- `devices_battery_low_total`  
- `near_red_zone_total`  
- `open_cases_total`  
- `cases_responded_24h_total`

**Dashboards (required)**  
- Devices below recommended battery  
- Devices near the red zone  
- Total alerts (by type)  
- SOS in the past 1 hour  
- Total tourists currently  
- Open cases  
- Cases responded in last 24 hours

---

## 8) E-FIR Draft Generation (per your format)
**When**: alert escalates to FIR threshold (e.g., prolonged SOS/inactivity).  
**Flow**: build draft JSON → officer review UI (outside this doc) → generate **PDF** (embedded last known map snapshot) → link in alert.

Use your provided sample JSON fields (kept verbatim for MVP).

---

## 9) SLOs & Acceptance Criteria
**SLOs**
- App ingest p95 ≤ **800 ms**, error ≤ **0.5%**  
- SOS → NEW alert create p95 ≤ **2 s**  
- Police stream event lag p95 ≤ **3 s**  
- Availability ≥ **99.9%**

**Acceptance**
- `POST /v1/app/ingest` returns score + nearest red-zone distance + advisories.  
- Entering red zone triggers `GEOFENCE` on Police stream within **≤5 s**.  
- Triggering SOS appears on stream within **≤2 s**; `POST /v1/police/ack` updates alert.  
- At least one tourist has an Ethereum testnet hash recorded & verifiable.

---

## 10) Ops Runbook (documentation-only)
1) Generate **root CA**, MoD **server cert**, and **client certs** (Police, Gateway).  
2) Start `mod-db`(2026), `keycloak`(2027), `prometheus`(2028), `grafana`(2029), `eth-adapter`, `mod-api`, `mod-proxy`(2025).  
3) Load Keycloak realm (tourist/police clients & roles).  
4) Seed: 1 tourist, itinerary anchors, 2 fences (1 red).  
5) Validate: ingest, fences summary, Police SSE, ACK, E-FIR draft, Grafana panels.
