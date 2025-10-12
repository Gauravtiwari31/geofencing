# MoD Core Integration Guide

## Overview

The Tourist Mobile Simulator automatically forwards telemetry and SOS payloads to the Ministry of Defence (MoD) Core ingest endpoint whenever the user authenticates via Keycloak. No additional toggles are required—once the UI login succeeds, every location/SOS event is sent to both the User Gateway and MoD Core.

```
Tourist Web UI → FastAPI backend
    ├── Gateway /gw/ingest (existing)
    └── MoD Core /v1/app/ingest (automatic once authenticated)
```

## Configuration

All configuration is handled via environment variables (or `.env`). Defaults are conservative so the feature is disabled until explicitly enabled.

| Variable | Default | Description |
|----------|---------|-------------|
| `MOD_CORE_ENABLE_FORWARDING` | `false` | Master switch; set to `true` to enable MoD Core forwarding |
| `MOD_CORE_BASE_URL` | `https://localhost:2025` | Base URL (mTLS proxy) for MoD Core |
| `MOD_CORE_INGEST_ENDPOINT` | `/v1/app/ingest` | Path added to the base URL |
| `MOD_CORE_TIMEOUT_SECONDS` | `10` | HTTP client timeout |
| `MOD_CORE_VERIFY_TLS` | `true` | If `false`, disables TLS verification (not recommended) |
| `MOD_CORE_CLIENT_CERT_PATH` | - | Path to client certificate (PEM) for mTLS |
| `MOD_CORE_CLIENT_KEY_PATH` | - | Path to client private key (PEM) |
| `MOD_CORE_CA_CERT_PATH` | - | Path to CA bundle required to verify MoD Core server certificate |

### Example `.env`

```
MOD_CORE_ENABLE_FORWARDING=true
MOD_CORE_BASE_URL=https://mod-core-proxy:2025
MOD_CORE_INGEST_ENDPOINT=/v1/app/ingest
MOD_CORE_CLIENT_CERT_PATH=/workspace/certs/tourist-sim.crt
MOD_CORE_CLIENT_KEY_PATH=/workspace/certs/tourist-sim.key
MOD_CORE_CA_CERT_PATH=/workspace/certs/mod-core-ca.pem
```

> **Note:** The simulator reuses the same OIDC access token obtained for the Gateway to authenticate with MoD Core. Ensure the Keycloak realm grants the `TOURIST` client role sufficient to call `/v1/app/ingest`.

## Payload Schema

MoD Core expects the following JSON body (as described in the MoD documentation). The simulator mirrors this model directly via `backend/models.py`:

```json
{
  "tourist_id": "uuid",
  "device_id": "device_hw_id",
  "position": {
    "lat": 26.162,
    "lng": 91.779,
    "alt": 53.4,
    "speed_mps": 0.0,
    "ts": "2025-09-24T14:30:30Z"
  },
  "health": {
    "heart_rate": 82,
    "fall_detected": false,
    "battery": 0.65
  },
  "sos": {
    "active": false
  },
  "app": {
    "build": "1.0.0",
    "platform": "android"
  }
}
```

The simulator currently sends the location + SOS information through the `IngestPayload` model. Extend `backend/models.py` with additional MoD fields (e.g., `tourist_id`, `health`, `app`) when those values are captured in the UI.

## Runtime Behaviour

- With forwarding **disabled**: `gateway_client.send_location` returns the Gateway response and notes that MoD Core forwarding is disabled.
- With forwarding **enabled**: the backend sends a secondary POST to `MOD_CORE_BASE_URL + MOD_CORE_INGEST_ENDPOINT`. Results are appended under the `mod_core` key in API responses.
- Failures (timeouts, TLS errors, HTTP 4xx/5xx) are captured and surfaced to the UI without blocking the primary Gateway call.

## Missing External Components

To establish a full end-to-end chain, provision the following systems (not bundled with the simulator):

1. **MoD Core HTTPS endpoint** on port **2025** (or 2030 without the mTLS proxy) exposing `/v1/app/ingest`.
2. **Client certificate + key** issued by MoD Core CA for the tourist simulator (used for mTLS).
3. **CA certificate bundle** trusted by the simulator to validate MoD Core’s server certificate.
4. **Keycloak realm** with the `tourist-app` client permitted to obtain tokens valid for both Gateway and MoD Core.

Without these dependencies, the simulator continues to operate in “Gateway-only” mode.

## Verification Checklist

- [ ] `MOD_CORE_ENABLE_FORWARDING=true`
- [ ] Certificates present at paths specified in `.env`
- [ ] Keycloak token contains audience/scope for MoD Core
- [ ] MoD Core `/v1/app/ingest` reachable from the container
- [ ] API responses show `"mod_core": {"status": "success"}`

Once the above items are in place, every location or SOS event originating from the map UI will be sent to both the User Gateway and the MoD Core ingest service automatically.
