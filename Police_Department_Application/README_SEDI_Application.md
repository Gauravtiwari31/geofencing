# Police SEDI Application — PRD (MVP)

## 0) Purpose
The **Police SEDI** consumes the MoD Core **response-oriented stream** and provides:
- Live **incidents** (SOS, irregular disconnections without prior notify, red-zone presence without confirmation).
- A small **map** showing only incident-related tourists (OSM/Leaflet; 10×10 m zoom; red polygons read-only).
- An **ACK** action that records police “responding” back to MoD Core.

**Constraints**
- Single host; IP calling; **ports 2025–2050** only.
- **No full telemetry or PII** locally; minimal incident mirror DB.

---

## 1) Components & Ports

| Component | Role                | Port map | Notes |
|---|---|---:|---|
| `sedi-web` | SEDI SPA (static)  | **2035:8080** | Uses OIDC with Keycloak; opens SSE to MoD |
| `sedi-db`  | PostgreSQL (police) | **2036:5432** | Minimal mirror: incidents & audit only |

Outbound to: `https://<MoD_IP>:2025` (mTLS + OIDC)

---

## 2) Security
- **OIDC** login via Keycloak (`POLICE` role).  
- Present **client cert** to MoD proxy (mTLS).  
- Store **no PII** beyond transient fields needed to render incidents.

---

## 3) Interfaces

### 3.1 Consume — SSE stream from MoD
`GET https://<MoD_IP>:2025/v1/police/stream`  
Auth: OIDC (`POLICE`) + client cert (mTLS)  
Cadence: snapshot every **5 s** + event on changes

Payload: see MoD PRD (§3.2). UI must tolerate additive fields.

### 3.2 Produce — ACK back to MoD
`POST https://<MoD_IP>:2025/v1/police/ack`  
Auth: OIDC (`POLICE`) + client cert  
Body:
```json
{ "alert_id": 987654, "tourist_id": "b1d0b691-...-9a", "note": "Unit dispatched", "officer_id": "ps-12-ajay" }
```

---

## 4) UX Requirements
- **Incidents**: list (type, tourist_id pseudonymous, created_at, status). Filters by type/time.  
- **Map**: OSM/Leaflet, shows **only incident tourists**, red polygons (read-only), zoom down to **10×10 m**.  
- **Details drawer**: last coordinate/time, score band, note.  
- **ACK** button: sends ACK; reflects in list and next stream snapshot.  
- **Resilience**: SSE auto-reconnect ≤ **3 s**; keep last snapshot in memory.

---

## 5) Local DB (minimal)
- `incidents (alert_id, tourist_id, type, created_at, last_status, last_update_at)`
- `actions (id, alert_id, officer_id, action, at, note)`
- `settings (key, value)`

> Not authoritative; used for UX speed and local audit.

---

## 6) SLOs & Acceptance
**SLOs**
- Render new incident ≤ **2 s** after event arrival (p95).  
- SSE reconnect ≤ **3 s** after loss.  
- UI responsive for ≤ **200** concurrent incidents.

**Acceptance**
- Connect to stream; snapshot & counts render.  
- SOS or red-zone event in MoD appears within **2 s**.  
- ACK posted; MoD stream reflects ACK on next update.

---

## 7) Ops Runbook (documentation-only)
1) Load **client cert** and OIDC config for SEDI.  
2) Start `sedi-db`(2036), `sedi-web`(2035).  
3) Operator logs in; verify incidents populate; perform test ACK.
