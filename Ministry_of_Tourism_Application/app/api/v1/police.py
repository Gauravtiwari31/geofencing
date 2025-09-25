"""
Police SSE streaming and ACK endpoints
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import PoliceUser
from app.models.alert import Alert
from app.models.tourist import Tourist, Location
from app.services.alert_engine import AlertEngine
from app.services.metrics import track_stream_event, update_stream_clients

logger = logging.getLogger(__name__)
router = APIRouter()

# Connected SSE clients tracking
connected_clients = set()


class PoliceAckRequest(BaseModel):
    alert_id: int
    tourist_id: str
    note: str = ""
    officer_id: str


class PoliceAckResponse(BaseModel):
    status: str
    at: datetime


async def generate_police_stream(db: Session) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events for police monitoring."""
    try:
        while True:
            # Get current snapshot
            snapshot_data = await get_police_snapshot(db)
            
            # Format as SSE
            event_data = json.dumps(snapshot_data, default=str)
            yield f"data: {event_data}\n\n"
            
            # Track metrics
            track_stream_event("snapshot")
            
            # Wait for next update (5 seconds as per spec)
            await asyncio.sleep(5)
            
    except asyncio.CancelledError:
        logger.info("Police stream cancelled")
        raise
    except Exception as e:
        logger.error(f"Error in police stream: {str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


async def get_police_snapshot(db: Session) -> Dict[str, Any]:
    """Get current police monitoring snapshot."""
    try:
        # Get total tourists being monitored
        tourists_monitored = db.query(Tourist).count()
        
        # Get active alerts by type
        active_alerts = {}
        for alert_type in ["sos", "geofence", "inactivity", "deviation", "vitals"]:
            count = db.query(Alert).filter(
                Alert.alert_type == alert_type.upper(),
                Alert.status.in_(["NEW", "ACK"])
            ).count()
            active_alerts[alert_type] = count
        
        # Get tourists with active issues
        tourists_with_issues = []
        
        # Get recent locations with alerts
        recent_locations = db.execute("""
            SELECT DISTINCT ON (l.tourist_id) 
                l.tourist_id, 
                ST_Y(l.geom) as lat, 
                ST_X(l.geom) as lon,
                l.recorded_at,
                l.metadata
            FROM locations l
            ORDER BY l.tourist_id, l.recorded_at DESC
            LIMIT 50
        """).fetchall()
        
        for location_data in recent_locations:
            tourist_id = location_data[0]
            
            # Get active alerts for this tourist
            active_alert = db.query(Alert).filter(
                Alert.tourist_id == tourist_id,
                Alert.status.in_(["NEW", "ACK"])
            ).order_by(Alert.created_at.desc()).first()
            
            if active_alert:
                # Calculate safety score (simplified for demo)
                location_metadata = location_data[4] or {}
                battery = location_metadata.get("battery", 1.0)
                
                # Simple score calculation
                score = 100
                if active_alert.alert_type == "SOS":
                    score = 0
                elif active_alert.priority == "CRITICAL":
                    score = 20
                elif active_alert.priority == "HIGH":
                    score = 40
                elif battery < 0.2:
                    score -= 20
                
                status_flags = []
                if active_alert.alert_type == "SOS":
                    status_flags.append("sos")
                if active_alert.alert_type == "GEOFENCE":
                    status_flags.append("geofence")
                if battery < 0.2:
                    status_flags.append("low_battery")
                
                tourist_data = {
                    "tourist_id": tourist_id,
                    "position": {
                        "lat": float(location_data[1]),
                        "lon": float(location_data[2]),
                        "ts": location_data[3].isoformat()
                    },
                    "score": score,
                    "status_flags": status_flags,
                    "last_alert": {
                        "alert_id": active_alert.id,
                        "type": active_alert.alert_type,
                        "ts": active_alert.created_at.isoformat()
                    }
                }
                tourists_with_issues.append(tourist_data)
        
        snapshot = {
            "snapshot_ts": datetime.utcnow().isoformat(),
            "totals": {
                "tourists_monitored": tourists_monitored,
                "active_alerts": active_alerts
            },
            "tourists": tourists_with_issues
        }
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Error generating police snapshot: {str(e)}")
        return {
            "snapshot_ts": datetime.utcnow().isoformat(),
            "error": str(e),
            "totals": {"tourists_monitored": 0, "active_alerts": {}},
            "tourists": []
        }


@router.get("/stream")
async def police_stream(
    request: Request,
    user: PoliceUser,
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events stream for police monitoring.
    Requires POLICE role and valid mTLS client certificate.
    """
    try:
        # Add client to tracking
        client_id = f"{request.client.host}_{datetime.utcnow().timestamp()}"
        connected_clients.add(client_id)
        update_stream_clients(len(connected_clients))
        
        logger.info(f"Police client connected: {client_id}")
        
        async def event_stream():
            try:
                async for data in generate_police_stream(db):
                    yield data
            except asyncio.CancelledError:
                logger.info(f"Police client disconnected: {client_id}")
            finally:
                # Remove client from tracking
                connected_clients.discard(client_id)
                update_stream_clients(len(connected_clients))
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error(f"Error setting up police stream: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to establish stream")


@router.post("/ack", response_model=PoliceAckResponse)
async def acknowledge_alert(
    ack_request: PoliceAckRequest,
    user: PoliceUser,
    db: Session = Depends(get_db)
):
    """
    Acknowledge an alert by police.
    Requires POLICE role and valid mTLS client certificate.
    """
    try:
        success = AlertEngine.acknowledge_alert(
            db=db,
            alert_id=ack_request.alert_id,
            officer_id=ack_request.officer_id,
            note=ack_request.note,
            action_taken="Police acknowledged"
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found or already resolved")
        
        logger.info(
            f"Alert {ack_request.alert_id} acknowledged by officer {ack_request.officer_id}"
        )
        
        return PoliceAckResponse(
            status="ACK",
            at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")
