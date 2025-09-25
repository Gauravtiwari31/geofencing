"""
Alert and incident models
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Alert(Base):
    """Alert lifecycle management."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tourist_id = Column(UUID(as_uuid=True), ForeignKey("tourists.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # SOS, GEOFENCE, INACTIVITY, VITALS, DEVIATION
    status = Column(String(20), default="NEW")  # NEW, ACK, RESOLVED, CANCELLED
    priority = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)
    location_lat = Column(String(20), nullable=True)
    location_lon = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ack_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Response tracking
    response_time_seconds = Column(Integer, nullable=True)
    escalated = Column(Boolean, default=False)
    police_notified = Column(Boolean, default=False)
    
    # Relationships
    tourist = relationship("Tourist", back_populates="alerts")
    acknowledgments = relationship("AlertAcknowledgment", back_populates="alert")


class AlertAcknowledgment(Base):
    """Police acknowledgments for alerts."""
    __tablename__ = "alert_acknowledgments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    officer_id = Column(String(255), nullable=False)
    note = Column(Text, nullable=True)
    action_taken = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    alert = relationship("Alert", back_populates="acknowledgments")


class IncidentReport(Base):
    """Incident reports and E-FIR drafts."""
    __tablename__ = "incident_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    tourist_id = Column(UUID(as_uuid=True), ForeignKey("tourists.id"), nullable=False)
    
    # E-FIR fields (as per your format)
    report_type = Column(String(50), default="EFIR")
    incident_type = Column(String(100), nullable=False)
    incident_datetime = Column(DateTime(timezone=True), nullable=False)
    location_description = Column(Text, nullable=True)
    complainant_details = Column(JSON, nullable=True)
    incident_details = Column(Text, nullable=True)
    
    # Status and workflow
    status = Column(String(20), default="DRAFT")  # DRAFT, SUBMITTED, PROCESSED
    generated_by = Column(String(255), nullable=True)
    pdf_path = Column(String(500), nullable=True)
    
    # Metadata
    alert_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Comprehensive audit trail."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String(255), nullable=False)  # user_id or system
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, VIEW, etc.
    entity_type = Column(String(50), nullable=False)  # Tourist, Alert, Geofence, etc.
    entity_id = Column(String(255), nullable=False)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    performed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    alert_metadata = Column(JSON, nullable=True)
