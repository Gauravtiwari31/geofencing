"""
MoD Core client integration
Handles secure Server-Sent Events (SSE) stream consumption and acknowledgements
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
import structlog

from config import settings
from models.schemas import (
    IncidentCreate,
    IncidentUpdate,
    LocationData,
    IncidentType,
    IncidentStatus,
    ScoreBand,
)
from models.database import AsyncSessionLocal
from services.sse_service import incident_broadcaster
from services.fir_service import generate_fir_pdf


logger = structlog.get_logger()


def _parse_timestamp(timestamp: Optional[str]) -> datetime:
    """Parse ISO8601 timestamp strings, defaulting to current UTC time."""
    if not timestamp:
        return datetime.now(timezone.utc)
    try:
        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"
        return datetime.fromisoformat(timestamp)
    except Exception:
        logger.warning("Failed to parse timestamp", raw=timestamp)
        return datetime.now(timezone.utc)


def _score_to_band(score: Optional[int]) -> Optional[ScoreBand]:
    if score is None:
        return None
    try:
        score = int(score)
    except ValueError:
        return None
    if score >= 80:
        return ScoreBand.HIGH
    if score >= 50:
        return ScoreBand.MEDIUM
    return ScoreBand.LOW


def _map_incident_type(raw_type: Optional[str]) -> IncidentType:
    if not raw_type:
        return IncidentType.DISCONNECTION
    upper_type = raw_type.upper()
    if upper_type in IncidentType.__members__:
        return IncidentType[upper_type]
    return IncidentType.DISCONNECTION


def _map_incident_status(raw_status: Optional[str], default: IncidentStatus) -> IncidentStatus:
    if not raw_status:
        return default
    upper_status = raw_status.upper()
    mapping = {
        "OPEN": IncidentStatus.ACTIVE,
        "ACK": IncidentStatus.ACKNOWLEDGED,
        "CLOSED": IncidentStatus.RESOLVED,
        "RESOLVED": IncidentStatus.RESOLVED,
        "ACTIVE": IncidentStatus.ACTIVE,
    }
    return mapping.get(upper_status, default)


class MoDCoreClient:
    """Client for interacting with MoD Core SSE stream and acknowledgement endpoint."""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._stream_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._lock = asyncio.Lock()
        self._token: Optional[str] = settings.mod_core_static_token
        self._token_expiry: Optional[datetime] = None
        self._status: Dict[str, Any] = {
            "enabled": settings.mod_core_enabled,
            "state": "disabled" if not settings.mod_core_enabled else "initializing",
            "last_event_received_at": None,
            "last_successful_connect_at": None,
            "last_error": None,
            "last_error_at": None,
            "active_alerts": 0,
            "totals": {},
        }

    async def start(self):
        if not settings.mod_core_enabled:
            logger.info("MoD Core integration disabled via configuration")
            return
        async with self._lock:
            if self._stream_task and not self._stream_task.done():
                return
            await self._ensure_http_client()
            self._stop_event.clear()
            self._stream_task = asyncio.create_task(self._run_stream())
            logger.info("MoD Core stream task started")

    async def stop(self):
        async with self._lock:
            self._stop_event.set()
            if self._stream_task:
                self._stream_task.cancel()
                try:
                    await self._stream_task
                except Exception:
                    pass
                self._stream_task = None
            if self._client:
                await self._client.aclose()
                self._client = None
            self._status["state"] = "stopped"

    async def _ensure_http_client(self):
        if self._client:
            return
        cert = None
        verify: Optional[str] = None

        if settings.mod_client_cert_path and settings.mod_client_key_path:
            cert = (settings.mod_client_cert_path, settings.mod_client_key_path)

        if settings.mod_ca_cert_path:
            verify = settings.mod_ca_cert_path
        else:
            verify = False

        timeout = httpx.Timeout(
            connect=10.0,
            read=settings.mod_core_stream_timeout_seconds,
            write=10.0,
            pool=10.0,
        )

        self._client = httpx.AsyncClient(
            base_url=settings.mod_core_url,
            cert=cert,
            verify=verify,
            timeout=timeout,
            headers={
                "User-Agent": "PoliceSEDI/1.0",
                "Accept": "text/event-stream",
            },
        )

    async def _run_stream(self):
        backoff = settings.mod_core_retry_delay_seconds
        while not self._stop_event.is_set():
            try:
                await self._ensure_http_client()
                headers = await self._build_auth_headers()
                async with self._client.stream(
                    "GET",
                    settings.mod_core_stream_path,
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    self._status.update(
                        {
                            "state": "connected",
                            "last_successful_connect_at": datetime.now(timezone.utc).isoformat(),
                            "last_error": None,
                            "last_error_at": None,
                        }
                    )
                    backoff = settings.mod_core_retry_delay_seconds
                    await self._consume_stream(response)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("MoD Core stream connection failed", error=str(exc), backoff_seconds=backoff)
                self._status.update(
                    {
                        "state": "degraded",
                        "last_error": str(exc),
                        "last_error_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                await asyncio.sleep(backoff)
                backoff = min(
                    backoff * settings.mod_core_retry_backoff_multiplier,
                    settings.mod_core_retry_max_delay_seconds,
                )

    async def _consume_stream(self, response: httpx.Response):
        buffer: List[str] = []
        async for line in response.aiter_lines():
            if self._stop_event.is_set():
                break
            if line == "":
                if buffer:
                    await self._process_event(buffer)
                    buffer.clear()
                continue
            buffer.append(line)
        if buffer:
            await self._process_event(buffer)

    async def _process_event(self, lines: List[str]):
        event_type = "message"
        data_lines: List[str] = []
        for line in lines:
            if line.startswith("event:"):
                event_type = line.split("event:", 1)[1].strip()
            elif line.startswith("data:"):
                data_lines.append(line.split("data:", 1)[1].strip())
        if not data_lines:
            return
        raw_data = "\n".join(data_lines)
        try:
            payload = json.loads(raw_data)
        except json.JSONDecodeError:
            logger.warning("Failed to decode MoD Core event", event=raw_data[:200])
            return
        handler = getattr(self, f"_handle_{event_type}", None)
        if callable(handler):
            await handler(payload)
        else:
            await self._handle_message(payload)

    async def _handle_message(self, payload: Dict[str, Any]):
        await self._process_snapshot(payload)

    async def _handle_ping(self, payload: Dict[str, Any]):  # pragma: no cover
        logger.debug("Received MoD Core ping", payload=payload)

    async def _process_snapshot(self, snapshot: Dict[str, Any]):
        tourists = snapshot.get("tourists", [])
        from services.incident_service import IncidentService

        async with AsyncSessionLocal() as session:
            created_incidents: List[Dict[str, Any]] = []
            updated_incidents: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
            for tourist in tourists:
                await self._sync_tourist_snapshot(session, tourist, created_incidents, updated_incidents)
            await session.commit()

        for incident_dict in created_incidents:
            await incident_broadcaster.incident_created(incident_dict)
        for incident_dict, changes in updated_incidents:
            if changes:
                await incident_broadcaster.incident_updated(incident_dict, changes)

        async with AsyncSessionLocal() as session:
            stats = await IncidentService.get_incident_statistics(session)
        await incident_broadcaster.stats_updated(stats.model_dump())

        self._status.update(
            {
                "state": "connected",
                "last_event_received_at": datetime.now(timezone.utc).isoformat(),
                "active_alerts": len(created_incidents) + len(updated_incidents),
                "totals": snapshot.get("totals", {}),
            }
        )

    async def _sync_tourist_snapshot(
        self,
        session,
        tourist: Dict[str, Any],
        created_incidents: List[Dict[str, Any]],
        updated_incidents: List[Tuple[Dict[str, Any], Dict[str, Any]]],
    ):
        from services.incident_service import IncidentService

        last_alert = tourist.get("last_alert") or {}
        alert_id = last_alert.get("alert_id")
        if not alert_id:
            return
        tourist_id = tourist.get("tourist_id") or "unknown"
        alert_type = _map_incident_type(last_alert.get("type"))
        alert_status = _map_incident_status(last_alert.get("status"), IncidentStatus.ACTIVE)
        created_at = _parse_timestamp(last_alert.get("ts"))
        score_band = _score_to_band(tourist.get("score"))

        position = tourist.get("position") or {}
        location = None
        if position.get("lat") is not None and position.get("lon") is not None:
            try:
                location = LocationData(
                    lat=float(position["lat"]),
                    lng=float(position["lon"]),
                    accuracy=int(position.get("accuracy", 50)),
                )
            except Exception:
                logger.warning("Invalid position data", position=position)

        details_parts = []
        status_flags = tourist.get("status_flags") or []
        if status_flags:
            details_parts.append(f"Flags: {', '.join(status_flags)}")
        battery = tourist.get("health", {}).get("battery")
        if battery is not None:
            try:
                percent = int(float(battery) * 100)
                details_parts.append(f"Battery: {percent}%")
            except Exception:
                pass
        if tourist.get("score") is not None:
            details_parts.append(f"Score: {tourist['score']}")
        if last_alert.get("note"):
            details_parts.append(f"Alert note: {last_alert['note']}")
        details = " | ".join(details_parts) if details_parts else None

        existing = await IncidentService.get_incident(session, alert_id)
        if existing is None:
            incident_data = IncidentCreate(
                alert_id=alert_id,
                tourist_id=tourist_id,
                type=alert_type,
                created_at=created_at,
                location=location,
                score_band=score_band,
                details=details,
            )
            fir_file = None
            if incident_data.location:
                try:
                    fir_file = generate_fir_pdf(incident_data.model_dump())
                except Exception as exc:
                    logger.warning("Failed to generate FIR PDF", error=str(exc))

            incident = await IncidentService.create_incident(session, incident_data, fir_pdf_path=fir_file)
            if alert_status != IncidentStatus.ACTIVE:
                await IncidentService.update_incident(
                    session,
                    alert_id,
                    IncidentUpdate(last_status=alert_status),
                )
                incident = await IncidentService.get_incident(session, alert_id)
            created_incidents.append(incident.to_dict())
        else:
            fir_file = existing.fir_pdf_path
            if not fir_file and location:
                try:
                    fir_file = generate_fir_pdf(
                        {
                            "alert_id": alert_id,
                            "tourist_id": tourist_id,
                            "type": alert_type.value,
                            "created_at": created_at,
                            "last_status": alert_status.value,
                            "location": location.model_dump() if location else None,
                            "score_band": score_band.value if score_band else None,
                            "details": details,
                        }
                    )
                except Exception as exc:
                    logger.warning("Failed to generate FIR PDF", error=str(exc))

            incident_update = IncidentUpdate(
                last_status=alert_status,
                location=location,
                score_band=score_band,
                details=details,
                fir_pdf_path=fir_file,
            )
            changes: Dict[str, Any] = {}
            if location and existing.location != location.model_dump():
                changes["location"] = location.model_dump()
            if score_band and existing.score_band != score_band.value:
                changes["score_band"] = score_band.value
            if details and existing.details != details:
                changes["details"] = details
            if existing.type != alert_type.value:
                changes["type"] = alert_type.value
            if existing.last_status != alert_status.value:
                changes["last_status"] = alert_status.value

            updated_incident = await IncidentService.update_incident(session, alert_id, incident_update)
            if updated_incident and changes:
                updated_incidents.append((updated_incident.to_dict(), changes))

    async def send_acknowledgement(self, alert_id: int, tourist_id: str, officer_id: str, note: Optional[str]):
        if not settings.mod_core_enabled:
            return
        await self._ensure_http_client()
        headers = await self._build_auth_headers()
        payload = {
            "alert_id": alert_id,
            "tourist_id": tourist_id,
            "officer_id": officer_id,
            "acknowledged_at": datetime.now(timezone.utc).isoformat(),
            "note": note,
        }
        try:
            response = await self._client.post(
                settings.mod_core_ack_path,
                headers=headers,
                json=payload,
                timeout=settings.mod_core_ack_timeout_seconds,
            )
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Failed to forward ACK to MoD Core", alert_id=alert_id, error=str(exc))

    async def _build_auth_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        token = await self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _get_token(self) -> Optional[str]:
        if self._token and self._token_expiry and datetime.now(timezone.utc) < self._token_expiry:
            return self._token
        if settings.mod_core_static_token:
            self._token = settings.mod_core_static_token
            self._token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
            return self._token
        if settings.mod_core_token_url and settings.mod_core_client_id and settings.mod_core_client_secret:
            try:
                async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                    data = {
                        "grant_type": "client_credentials",
                        "client_id": settings.mod_core_client_id,
                        "client_secret": settings.mod_core_client_secret,
                    }
                    if settings.mod_core_token_scope:
                        data["scope"] = settings.mod_core_token_scope
                    if settings.mod_core_token_audience:
                        data["audience"] = settings.mod_core_token_audience
                    response = await client.post(
                        settings.mod_core_token_url,
                        data=data,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                    response.raise_for_status()
                    token_data = response.json()
                    self._token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 3600)
                    self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 30)
                    logger.info("Obtained token from Keycloak", expires_in=expires_in)
                    return self._token
            except Exception as exc:
                logger.error("Failed to obtain token from Keycloak", error=str(exc))
        return self._token

    def health_status(self) -> Dict[str, Any]:
        return dict(self._status)

    def _map_incident_for_frontend(self, incident) -> Dict[str, Any]:
        """Convert ORM incident to dict with map-friendly location."""
        data = incident.to_dict()
        location = data.get("location")
        if location and isinstance(location, dict):
            try:
                data["location"] = {
                    "lat": float(location.get("lat")),
                    "lng": float(location.get("lng")),
                    "accuracy": location.get("accuracy"),
                }
            except Exception:
                data["location"] = None
        return data


mod_core_client = MoDCoreClient()


