# User App Gateway (Tourist-Side) — PRD (MVP)

## 0) Purpose
The **User App Gateway** is the tourist-side ingress that:
- **Verifies tokens** (OIDC/“digital-ID JWT”) and screens traffic before MoD Core.
- Proxies **tourist app** calls to MoD Core with **rate limits** and correlation IDs.
- Hosts **Mosquitto** to accept **ESP32** telemetry/SOS (via tourist Wi-Fi/phone hotspot) and **forwards** validated messages to MoD Core’s ingest.
- Manages minimal **preferences** (locale, consent).  
- For MVP, **Gateway is mandatory** path to MoD for the app.

**Constraints**
- Single host; IP calling; **ports 2025–2050** only.

---

## 1) Components & Ports

| Component   | Role                                   | Port map | Notes |
|---|---|---:|---|
| `gw-api`    | Gateway API (verify + proxy + prefs)   | **2045:8080** | Forwards to MoD over **mTLS** |
| `mosquitto` | MQTT broker (ESP32 intake)             | **2046:1883** | Local-only; do not expose to WAN |
| `gw-db`     | Lightweight DB (prefs/devices/audit)   | **2048:5432** | Could be sqlite if preferred |

Outbound to: `https://<MoD_IP>:2025` (mTLS + OIDC)

---

## 2) Security & Verification
- **Token screening**:  
  - Validate **Keycloak OIDC JWT** or **digital-ID JWT** signature (public JWKS) and optionally cross-check against on-chain hash.  
  - If valid → forward; else **reject** immediately.
- **MoD transport**:  
  - Gateway presents **client cert** to MoD proxy (mTLS).  
  - All forwards include correlation IDs and sanitized payloads.
- **Rate limits**: per tourist avg **1/min**; bursts on SOS allowed; hard caps to prevent abuse.

---

## 3) Gateway API

### 3.1 App proxy
`POST /gw/ingest` → forwards to `MoD /v1/app/ingest`  
- Auth: App sends OIDC token; Gateway validates before forwarding.  
- Adds `X-Correlation-Id`, enforces rate limit, logs audit event.

`GET /gw/messages` → forwards to `MoD /v1/app/messages`  
`POST /gw/register-device` → (device ↔ tourist) association
```json
{ "tourist_id": "b1d0b691-...-9a", "device_id": "esp32-mac-xx", "secret_hint": "optional" }
```

### 3.2 ESP32 ingress
- **MQTT topics** (ESP32 → Gateway Mosquitto):
  - `esp32/{deviceId}/telemetry` payload: `{"ts":"...", "hr":..., "accel":[...], "bat":0.73}`
  - `esp32/{deviceId}/sos` payload: `{"ts":"...", "lat":..., "lon":...}`
  - Device **must be registered**; (optional) HMAC signing in payload for MVP.
- **HTTPS fallback**: `POST /gw/esp32/sos`
```json
{ "device_id": "esp32-mac-xx", "lat": 26.162, "lon": 91.779, "ts": "2025-09-24T14:31:00Z" }
```
- Forwarding logic: Gateway transforms ESP32 messages to the **MoD `/v1/app/ingest`** contract with `sos.active=true` and/or health fields.

---

## 4) Preferences & Localization
- Store per-tourist `locale`, `consent.live_share`.  
- **Server-side localization** strategy adopted, but **English-only** strings in MVP.

---

## 5) Data Minimization
- Gateway DB contains: `devices (tourist_id, device_id)`, `prefs (locale, consent)`, `audit (who/what/when)`.  
- No long-term telemetry retention at Gateway.

---

## 6) SLOs & Acceptance
**SLOs**
- Gateway adds ≤ **100 ms** p95 latency over direct MoD call.  
- MQTT intake → MoD forward ≤ **2 s** p95.  
- Availability ≥ **99.9%**.

**Acceptance**
- App uses `/gw/ingest` and receives valid MoD response.  
- ESP32 publishes to `esp32/{deviceId}/sos` → MoD alert appears on Police SEDI.  
- Invalid tokens/devices are rejected at Gateway.

---

## 7) Ops Runbook (documentation-only)
1) Import Keycloak JWKS & configure verification; install **client cert** for MoD mTLS.  
2) Start `mosquitto`(2046), `gw-db`(2048), `gw-api`(2045).  
3) Register a tourist and device; test `/gw/ingest` success path.  
4) Publish test MQTT SOS; verify MoD stream & Police SEDI receipt.

---

## 8) ESP32 Connectivity Guidance
- Default: **phone hotspot** or local Wi-Fi to reach Gateway `mqtt://<GATEWAY_IP>:2046`.  
- HTTPS fallback for SOS: `http(s)://<GATEWAY_IP>:2045/gw/esp32/sos`.  
- Keep broker non-public; treat as **local edge intake**.
