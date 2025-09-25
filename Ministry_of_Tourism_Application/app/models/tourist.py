"""
Tourist and related models
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Float, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from app.core.database import Base


class Tourist(Base):
    """Tourist entity with digital identity."""
    __tablename__ = "tourists"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    digital_id_hash = Column(String(64), unique=True, nullable=True)
    id_expiry = Column(DateTime(timezone=True), nullable=True)
    emergency_contact = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    devices = relationship("Device", back_populates="tourist")
    locations = relationship("Location", back_populates="tourist")
    alerts = relationship("Alert", back_populates="tourist", lazy="dynamic")
    digital_ids = relationship("DigitalId", back_populates="tourist")
    consents = relationship("Consent", back_populates="tourist", uselist=False)


class DigitalId(Base):
    """Digital identity verification records."""
    __tablename__ = "digital_ids"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tourist_id = Column(UUID(as_uuid=True), ForeignKey("tourists.id"), nullable=False)
    offchain_hash = Column(String(64), nullable=False)
    eth_tx_hash = Column(String(66), nullable=True)
    chain = Column(String(20), default="sepolia")
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    tourist = relationship("Tourist", back_populates="digital_ids")


class Device(Base):
    """Tourist devices for telemetry."""
    __tablename__ = "devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tourist_id = Column(UUID(as_uuid=True), ForeignKey("tourists.id"), nullable=False)
    hw_id = Column(String(255), unique=True, nullable=False)
    device_type = Column(String(50), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    device_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    tourist = relationship("Tourist", back_populates="devices")
    locations = relationship("Location", back_populates="device")


class Location(Base):
    """Tourist location tracking."""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tourist_id = Column(UUID(as_uuid=True), ForeignKey("tourists.id"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    geom = Column(Geography("POINT", srid=4326), nullable=False)
    speed_mps = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    location_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    tourist = relationship("Tourist", back_populates="locations")
    device = relationship("Device", back_populates="locations")


class Consent(Base):
    """Tourist consent management."""
    __tablename__ = "consents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tourist_id = Column(UUID(as_uuid=True), ForeignKey("tourists.id"), nullable=False)
    live_share = Column(Boolean, default=True)
    retention_days = Column(Integer, default=30)
    emergency_sharing = Column(Boolean, default=True)
    police_sharing = Column(Boolean, default=True)
    analytics_sharing = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tourist = relationship("Tourist", back_populates="consents")
