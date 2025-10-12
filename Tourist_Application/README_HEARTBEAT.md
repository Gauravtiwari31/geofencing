# Heartbeat Sender (Auth-less)

A minimal headless script that sends a location heartbeat every N seconds to your ingest endpoint without any authentication.

## Run

```bash
cd /workspace
pip install -r requirements.txt
python heartbeat.py
```
## Server
```bash
python -m http.server 2040 --directory /workspace/web
```

## Configuration (env)

- `TARGET_URL` (default: `http://localhost:2030/v1/app/ingest`)
- `HEARTBEAT_SECONDS` (default: `5`)
- `START_LAT` (default: `26.1625`)
- `START_LNG` (default: `91.7794`)
- `JITTER_METERS` (default: `3`) – random walk per tick
- `DEVICE_ID` (default: `tourist-sim-001`)
- `APP_BUILD_VERSION` (default: `1.0.0`)
- `APP_PLATFORM` (default: `headless`)

Example:

```bash
export TARGET_URL=http://localhost:2030/v1/app/ingest
export HEARTBEAT_SECONDS=5
export START_LAT=26.1625
export START_LNG=91.7794
python heartbeat.py
```

## Payload Format

```json
{
  "tourist_id": null,
  "device_id": "tourist-sim-001",
  "position": {
    "lat": 26.1625,
    "lng": 91.7794,
    "alt": null,
    "speed_mps": null,
    "ts": "2025-09-25T14:30:30Z"
  },
  "health": {
    "heart_rate": null,
    "fall_detected": null,
    "battery": null
  },
  "sos": null,
  "app": {
    "build": "1.0.0",
    "platform": "headless"
  }
}
```

This aligns with the current ingest payload shape used by the simulator. Adjust `TARGET_URL` to point directly to MoD Core or a gateway as needed.
