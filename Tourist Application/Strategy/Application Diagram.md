## Mermaid (copy–paste as-is)

```mermaid
flowchart TB

%% LAYER 1 — REGISTRATION & DIGITAL ID
subgraph REG["Tourist Registration & Digital ID"]
  R1[KYC + Itinerary Input]
  B1[Blockchain: Digital ID Issuance (hash / pointer only)]
  V1[ID Verify API (on-chain check + off-chain profile)]
  R1 --> B1 --> V1
end

%% LAYER 2 — MOBILE APP
subgraph APP["Tourist Mobile App"]
  M1[Login via Digital ID / OIDC]
  M2[Live Location Tracking (background)]
  M3[Geo-fencing Alerts]
  M4[SOS Panic Button]
  M5[Safety Score Display]
  M6[Opt-in Live Sharing]
  M7[Offline Store-and-Forward + SMS fallback]
end

%% LAYER 3 — IOT (ESP32 WEARABLE)
subgraph IOT["ESP32 Wearable"]
  I1[SOS Button]
  I2[Vitals / Accelerometer]
  I5[BLE → Mobile Relay]
  I6[Wi-Fi → Direct MQTT / HTTPS]
  I3[(Device Registry)]
  I4[(MQTT Broker)]
end

%% LAYER 4 — BACKEND & AI
subgraph BE["Backend & AI"]
  A0[AuthN / AuthZ (Keycloak, RBAC, Audit)]
  A1[Ingestion API (REST / WebSocket / MQTT)]
  A2[Queue / Topic]
  A3[Rules + ML Scorer (inactivity, deviation, geofence, vitals)]
  A4[Alert Processor & Orchestrator]
  A5[Notification Service (FCM / APNs / SMS / e-mail / 112 handoff)]
  A6[E-FIR Generator (PDF)]
  A7[(Operational DB: Postgres + PostGIS)]
  A8[(Time-series Store: Timescale / ClickHouse)]
  A9[(Object Store: KYC scans, E-FIR)]
  A10[Risk Zone Store & Editor]
  A11[Consent & Retention Policy]
  A12[Observability (Logs / Metrics / Tracing)]
end

%% LAYER 5 — AUTHORITY DASHBOARD
subgraph DASH["Authority Dashboard"]
  D1[Secure Login (RBAC)]
  D2[Live Tourist Map + Heatmaps]
  D3[Alert / Incident Panel]
  D4[Tourist Profile + ID Verify]
  D5[Geofence Editor]
  D6[Resolve / Acknowledge Workflow]
  D7[Analytics / Reports]
end

%% FLOWS — APP → BACKEND
M1 --> A0
M2 --> A1
M3 --> A1
M4 --> A1
M6 --> A1
M7 --> A1

%% FLOWS — ESP32 PATHS
I1 --> I5 --> M4
I2 --> I5 --> M2
I1 --> I6 --> A1
I2 --> I6 --> A1
I3 --- A1
I4 --- A1

%% FLOWS — PROCESSING
A1 --> A2 --> A3 --> A4
A10 --> M3
A10 --> A3
A4 --> A5
A4 --> A6
A4 --> D3
A4 --> D2

%% DATA STORES
A1 --> A7
A4 --> A7
A1 --> A8
A6 --> A9

%% DASHBOARD USAGE
D1 --> D2
D1 --> D3
D1 --> D4
D1 --> D5
D1 --> D6
D1 --> D7
D4 --> V1
D5 --> A10

%% REGISTRATION LINKS
R1 --> B1
B1 --> V1
V1 --> D4

%% CROSS-CUTTING
A0 --- D1
A0 --- A1
A11 --- M6
A11 --- A7
A12 --- A1
A12 --- A3
A12 --- A4
```

---

## ASCII (print-friendly)

```
                          ┌───────────────────────────────────────────────┐
                          │   TOURIST REGISTRATION & DIGITAL ID           │
                          │   - KYC + Itinerary Input                     │
                          │   - Blockchain: Digital ID Issuance           │
                          │     (hash/pointer only, no PII on-chain)      │
                          │   - ID Verify API (on-chain + off-chain)      │
                          └───────────────┬───────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               TOURIST MOBILE APP                                    │
│  Login (Digital ID/OIDC)                                                            │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐       │
│  │ Live Track   │ Geofencing   │ SOS Panic    │ Safety Score │ Live Sharing │       │
│  │ (background) │ Alerts       │ Button       │ Display      │ (opt-in)     │       │
│  └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘       │
│  Offline store-and-forward + SMS fallback                                           │
└───────────────┬─────────────────────────────────────────────────────────────────────┘
                │  BLE relay (from ESP32)                         Wi-Fi direct
                │                                                (ESP32 → MQTT/HTTPS)
                │                                                       │
                ▼                                                       ▼
     ┌──────────────────────┐                                   ┌──────────────────────┐
     │   ESP32 WEARABLE     │                                   │   IOT INGEST PATH    │
     │  - SOS Button        │───(BLE→Mobile)──────────────────▶│  MQTT Broker / HTTPS  │
     │  - Vitals/Accel      │                                   │  Device Registry     │
     └──────────────────────┘                                   └──────────────────────┘

                          ┌──────────────────── BACKEND & AI ────────────────────┐
                          │  AuthN/AuthZ (Keycloak, RBAC, audit)                 │
                          │  Ingestion API (REST/WebSocket/MQTT)                 │
                          │  Queue/Topic                                         │
                          │  Rules + ML Scorer (inactivity, deviation, geofence, │
                          │                   vitals)                            │
                          │  Alert Orchestrator → Notification Service           │
                          │      (FCM/APNs, SMS/e-mail, 112 handoff)             │
                          │  E-FIR Generator (PDF)                               │
                          │  Risk Zone Store & Editor                            │
                          │  Consent & Retention Policy                          │
                          │  Observability (logs/metrics/tracing)                │
                          └──────────┬───────────────┬─────────────────────────┬─┘
                                     │               │                         │
                         ┌───────────▼──────────┐  ┌─▼─────────────────┐  ┌────▼───────────────┐
                         │ Operational DB       │  │ Time-series Store │  │ Object Store       │
                         │ Postgres + PostGIS   │  │ Timescale/ClickH. │  │ KYC scans, E-FIR   │
                         └──────────────────────┘  └───────────────────┘  └────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  AUTHORITY DASHBOARD                                │
│  Secure Login (RBAC)                                                                 │
│  Live Tourist Map + Heatmaps   |  Alert/Incident Panel  |  Tourist Profile + Verify │
│  Geofence Editor               |  Resolve/Acknowledge   |  Analytics/Reports        │
│     ▲                          |                        |                            │
│     │ uses ID Verify API       | receives alerts from backend                        │
└─────┴────────────────────────────────────────────────────────────────────────────────┘
```