"""
Geofencing models
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geography
from app.core.database import Base


class Geofence(Base):
    """Geofence polygons with safety levels."""
    __tablename__ = "geofences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Integer, nullable=False)  # 1-10 scale, 10 being most dangerous
    geom = Column(Geography("POLYGON", srid=4326), nullable=False)
    active = Column(Boolean, default=True)
    zone_type = Column(String(50), nullable=False)  # red_zone, restricted, caution, etc.
    geofence_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)


class GeofenceEvent(Base):
    """Records of geofence entry/exit events."""
    __tablename__ = "geofence_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tourist_id = Column(UUID(as_uuid=True), nullable=False)
    geofence_id = Column(Integer, nullable=False)
    event_type = Column(String(20), nullable=False)  # enter, exit
    location = Column(Geography("POINT", srid=4326), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    alert_generated = Column(Boolean, default=False)
    geofence_metadata = Column(JSON, nullable=True)
