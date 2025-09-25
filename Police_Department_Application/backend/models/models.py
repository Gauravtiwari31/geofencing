"""
SQLAlchemy models for Police SEDI database
Maps to the PostgreSQL schema defined in database/init.sql
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, JSON, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class Incident(Base):
    """
    Incident model - minimal mirror of incidents from MoD Core
    Stores only essential data for police operations
    """
    __tablename__ = "incidents"

    alert_id = Column(BigInteger, primary_key=True, index=True)
    tourist_id = Column(String(36), nullable=False, index=True)
    type = Column(
        String(20), 
        nullable=False, 
        index=True
    )
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_status = Column(
        String(20), 
        nullable=False, 
        index=True,
        default="ACTIVE"
    )
    last_update_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    location = Column(JSONB, nullable=True)  # {"lat": float, "lng": float, "accuracy": int}
    score_band = Column(String(10), nullable=True)
    details = Column(Text, nullable=True)

    # Relationships
    actions = relationship("Action", back_populates="incident", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("type IN ('SOS', 'RED_ZONE', 'DISCONNECTION')", name='check_incident_type'),
        CheckConstraint("last_status IN ('ACTIVE', 'ACKNOWLEDGED', 'RESOLVED')", name='check_incident_status'),
        CheckConstraint("score_band IN ('HIGH', 'MEDIUM', 'LOW') OR score_band IS NULL", name='check_score_band'),
    )

    def __repr__(self):
        return f"<Incident(alert_id={self.alert_id}, type={self.type}, status={self.last_status})>"

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "alert_id": self.alert_id,
            "tourist_id": self.tourist_id,
            "type": self.type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_status": self.last_status,
            "last_update_at": self.last_update_at.isoformat() if self.last_update_at else None,
            "location": self.location,
            "score_band": self.score_band,
            "details": self.details
        }

    @property
    def is_active(self) -> bool:
        """Check if incident is still active"""
        return self.last_status == "ACTIVE"

    @property
    def is_acknowledged(self) -> bool:
        """Check if incident has been acknowledged"""
        return self.last_status in ("ACKNOWLEDGED", "RESOLVED")

    @property
    def urgency_score(self) -> int:
        """Get urgency score for sorting (higher = more urgent)"""
        type_scores = {"SOS": 100, "RED_ZONE": 50, "DISCONNECTION": 25}
        band_scores = {"HIGH": 30, "MEDIUM": 20, "LOW": 10}
        status_scores = {"ACTIVE": 10, "ACKNOWLEDGED": 5, "RESOLVED": 0}
        
        return (
            type_scores.get(self.type, 0) + 
            band_scores.get(self.score_band, 0) + 
            status_scores.get(self.last_status, 0)
        )


class Action(Base):
    """
    Action model - audit log of police actions on incidents
    Records all interactions for accountability and tracking
    """
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(BigInteger, ForeignKey("incidents.alert_id", ondelete="CASCADE"), nullable=False, index=True)
    officer_id = Column(String(50), nullable=False, index=True)
    action = Column(String(20), nullable=False)
    performed_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    note = Column(Text, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="actions")

    # Constraints
    __table_args__ = (
        CheckConstraint("action IN ('ACK', 'VIEW', 'NOTE')", name='check_action_type'),
    )

    def __repr__(self):
        return f"<Action(id={self.id}, alert_id={self.alert_id}, action={self.action}, officer={self.officer_id})>"

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "officer_id": self.officer_id,
            "action": self.action,
            "performed_at": self.performed_at.isoformat() if self.performed_at else None,
            "note": self.note
        }


class Setting(Base):
    """
    Setting model - application configuration and state storage
    Key-value store for application settings and runtime state
    """
    __tablename__ = "settings"

    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Setting(key={self.key}, value={self.value[:50]}...)>"

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    async def get_value(cls, session, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get setting value by key"""
        from sqlalchemy import select
        
        result = await session.execute(select(cls).where(cls.key == key))
        setting = result.scalar_one_or_none()
        return setting.value if setting else default

    @classmethod
    async def set_value(cls, session, key: str, value: str) -> "Setting":
        """Set setting value by key"""
        from sqlalchemy import select
        
        result = await session.execute(select(cls).where(cls.key == key))
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
            setting.updated_at = func.now()
        else:
            setting = cls(key=key, value=value)
            session.add(setting)
        
        return setting
