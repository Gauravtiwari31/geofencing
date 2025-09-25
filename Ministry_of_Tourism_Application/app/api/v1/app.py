"""
Tourist Mobile API endpoints
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_Distance, ST_GeomFromText, ST_DWithin
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import TouristUser
from app.models.tourist import Tourist, Device, Location
from app.models.alert import Alert
from app.models.geofence import Geofence
from app.services.safety_scoring import calculate_safety_score
from app.services.geofencing import check_geofence_violations, get_nearest_red_zone_distance
from app.services.alert_engine import process_telemetry_for_alerts
from app.services.metrics import track_alert_created, update_tourist_count

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class PositionData(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    alt: Optional[float] = None
    speed_mps: Optional[float] = Field(None, ge=0)
    ts: datetime


class HealthData(BaseModel):
    heart_rate: Optional[int] = Field(None, ge=30, le=250)
    fall_detected: bool = False
    battery: float = Field(..., ge=0, le=1)


class SOSData(BaseModel):
    active: bool = False


class AppData(BaseModel):
    build: str
    platform: str


class TelemetryRequest(BaseModel):
    tourist_id: str
    device_id: str
    position: PositionData
    health: HealthData
    sos: SOSData
    app: AppData


class SafetyResponse(BaseModel):
    score: int = Field(..., ge=0, le=100)
    red_zone_distance_m: Optional[float]
    in_red_zone: bool


class TelemetryResponse(BaseModel):
    ack: bool = True
    safety: SafetyResponse
    advisories: List[str] = []
    open_alert: Optional[Dict[str, Any]] = None


class FencesSummaryResponse(BaseModel):
    red_zone_distance_m: Optional[float]
    in_red_zone: bool
    nearest_zone_name: Optional[str] = None


class MessageResponse(BaseModel):
    messages: List[str]
    last_updated: datetime


# Idempotency tracking (in production, use Redis)
_idempotency_cache = {}


def check_idempotency(key: str) -> bool:
    """Check if request has been processed before."""
    if key in _idempotency_cache:
        return True
    _idempotency_cache[key] = datetime.utcnow()
    return False


@router.post("/ingest", response_model=TelemetryResponse)
async def ingest_telemetry(
    telemetry: TelemetryRequest,
    background_tasks: BackgroundTasks,
    user: TouristUser,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
    """
    Ingest tourist telemetry and return contextual safety information.
    
    - **telemetry**: Tourist device telemetry data
    - **idempotency_key**: Optional idempotency key for deduplication
    """
    try:
        # Check idempotency
        if idempotency_key and check_idempotency(idempotency_key):
            logger.warning(f"Duplicate request with key: {idempotency_key}")
            raise HTTPException(status_code=409, detail="Request already processed")
        
        # Verify tourist access
        if user.tourist_id != telemetry.tourist_id:
            raise HTTPException(status_code=403, detail="Access denied to tourist data")
        
        # Get or create tourist
        tourist = db.query(Tourist).filter(Tourist.id == telemetry.tourist_id).first()
        if not tourist:
            raise HTTPException(status_code=404, detail="Tourist not found")
        
        # Get or create device
        device = db.query(Device).filter(
            Device.hw_id == telemetry.device_id,
            Device.tourist_id == telemetry.tourist_id
        ).first()
        
        if not device:
            device = Device(
                tourist_id=telemetry.tourist_id,
                hw_id=telemetry.device_id,
                device_type=telemetry.app.platform,
                last_seen=datetime.utcnow()
            )
            db.add(device)
            db.commit()
            db.refresh(device)
        else:
            device.last_seen = datetime.utcnow()
            db.commit()
        
        # Create location record
        location_point = f"POINT({telemetry.position.lon} {telemetry.position.lat})"
        location = Location(
            tourist_id=telemetry.tourist_id,
            device_id=device.id,
            recorded_at=telemetry.position.ts,
            geom=location_point,
            speed_mps=telemetry.position.speed_mps,
            altitude=telemetry.position.alt,
            location_metadata={
                "heart_rate": telemetry.health.heart_rate,
                "fall_detected": telemetry.health.fall_detected,
                "battery": telemetry.health.battery,
                "app_build": telemetry.app.build
            }
        )
        db.add(location)
        db.commit()
        
        # Calculate safety metrics
        red_zone_distance = get_nearest_red_zone_distance(
            db, telemetry.position.lat, telemetry.position.lon
        )
        
        in_red_zone = red_zone_distance is not None and red_zone_distance <= 0
        
        # Check for geofence violations
        violations = check_geofence_violations(
            db, telemetry.position.lat, telemetry.position.lon
        )
        
        # Calculate safety score
        safety_data = {
            "in_red_zone": in_red_zone,
            "red_zone_distance_m": red_zone_distance,
            "health": telemetry.health.dict(),
            "sos": telemetry.sos.dict(),
            "violations": violations
        }
        
        safety_score = calculate_safety_score(safety_data)
        
        # Generate advisories
        advisories = []
        if red_zone_distance and red_zone_distance < 500:
            advisories.append("You are approaching a restricted area. Please maintain safe distance.")
        if telemetry.health.battery < 0.2:
            advisories.append("Device battery is low. Please charge soon.")
        if telemetry.health.heart_rate and telemetry.health.heart_rate > 100:
            advisories.append("Elevated heart rate detected. Take rest if needed.")
        
        # Process alerts in background
        background_tasks.add_task(
            process_telemetry_for_alerts,
            db, telemetry.dict(), safety_data
        )
        
        # Check for open alerts
        open_alert = db.query(Alert).filter(
            Alert.tourist_id == telemetry.tourist_id,
            Alert.status.in_(["NEW", "ACK"])
        ).first()
        
        # Update metrics
        tourist_count = db.query(Tourist).count()
        update_tourist_count(tourist_count)
        
        # Prepare response
        safety_response = SafetyResponse(
            score=safety_score,
            red_zone_distance_m=red_zone_distance,
            in_red_zone=in_red_zone
        )
        
        response = TelemetryResponse(
            safety=safety_response,
            advisories=advisories,
            open_alert=open_alert.payload if open_alert else None
        )
        
        logger.info(
            f"Processed telemetry for tourist {telemetry.tourist_id}, "
            f"safety score: {safety_score}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing telemetry: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/fences/summary", response_model=FencesSummaryResponse)
async def get_fences_summary(
    lat: float,
    lon: float,
    user: TouristUser,
    db: Session = Depends(get_db)
):
    """
    Get quick summary of nearest geofences for the given location.
    
    - **lat**: Latitude
    - **lon**: Longitude
    """
    try:
        # Get nearest red zone distance
        red_zone_distance = get_nearest_red_zone_distance(db, lat, lon)
        in_red_zone = red_zone_distance is not None and red_zone_distance <= 0
        
        # Get nearest zone name
        nearest_zone_name = None
        if red_zone_distance is not None:
            point = f"POINT({lon} {lat})"
            nearest_zone = db.query(Geofence).filter(
                Geofence.active == True,
                Geofence.zone_type == "red_zone"
            ).order_by(
                ST_Distance(Geofence.geom, ST_GeomFromText(point, 4326))
            ).first()
            
            if nearest_zone:
                nearest_zone_name = nearest_zone.name
        
        return FencesSummaryResponse(
            red_zone_distance_m=red_zone_distance,
            in_red_zone=in_red_zone,
            nearest_zone_name=nearest_zone_name
        )
        
    except Exception as e:
        logger.error(f"Error getting fences summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/messages", response_model=MessageResponse)
async def get_messages(
    user: TouristUser,
    db: Session = Depends(get_db)
):
    """
    Get localized messages and advisories for the tourist.
    Currently returns English messages only (MVP).
    """
    try:
        # Get tourist-specific messages
        tourist = db.query(Tourist).filter(Tourist.id == user.tourist_id).first()
        if not tourist:
            raise HTTPException(status_code=404, detail="Tourist not found")
        
        # Get recent alerts for context
        recent_alerts = db.query(Alert).filter(
            Alert.tourist_id == user.tourist_id,
            Alert.status.in_(["NEW", "ACK"])
        ).limit(5).all()
        
        # Generate contextual messages
        messages = [
            "Welcome to our tourism safety system.",
            "Keep your device charged and connected.",
            "Follow local guidelines and stay in safe areas."
        ]
        
        # Add alert-specific messages
        for alert in recent_alerts:
            if alert.alert_type == "GEOFENCE":
                messages.append("Please avoid restricted areas for your safety.")
            elif alert.alert_type == "VITALS":
                messages.append("Take care of your health during travel.")
        
        # Add low battery warning if needed
        recent_location = db.query(Location).filter(
            Location.tourist_id == user.tourist_id
        ).order_by(Location.recorded_at.desc()).first()
        
        if recent_location and recent_location.location_metadata:
            battery = recent_location.location_metadata.get("battery", 1.0)
            if battery < 0.3:
                messages.append("Your device battery is getting low. Please charge it soon.")
        
        return MessageResponse(
            messages=messages,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
