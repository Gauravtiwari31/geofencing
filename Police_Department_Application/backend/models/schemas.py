"""
Pydantic schemas for API request/response validation
Defines the data models for FastAPI endpoints
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, validator


class IncidentType(str, Enum):
    """Incident type enumeration"""
    SOS = "SOS"
    RED_ZONE = "RED_ZONE"
    DISCONNECTION = "DISCONNECTION"
    GEOFENCE = "GEOFENCE"
    INACTIVITY = "INACTIVITY"


class IncidentStatus(str, Enum):
    """Incident status enumeration"""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class ScoreBand(str, Enum):
    """Score band enumeration"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ActionType(str, Enum):
    """Action type enumeration"""
    ACK = "ACK"
    VIEW = "VIEW"
    NOTE = "NOTE"


class LocationData(BaseModel):
    """Location information model"""
    lat: float = Field(..., description="Latitude coordinate")
    lng: float = Field(..., description="Longitude coordinate")  
    accuracy: int = Field(..., description="Location accuracy in meters")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "lat": 40.7128,
                "lng": -74.0060,
                "accuracy": 10
            }
        }
    )


# Incident Schemas
class IncidentBase(BaseModel):
    """Base incident schema"""
    tourist_id: str = Field(..., description="Pseudonymous tourist identifier")
    type: IncidentType = Field(..., description="Type of incident")
    location: Optional[LocationData] = Field(None, description="Location information")
    score_band: Optional[ScoreBand] = Field(None, description="Risk/urgency score band")
    details: Optional[str] = Field(None, description="Additional incident details")
    fir_pdf_path: Optional[str] = Field(None, description="Path to generated FIR PDF")


class IncidentCreate(IncidentBase):
    """Schema for creating incidents"""
    alert_id: int = Field(..., description="Unique alert identifier from MoD Core")
    created_at: datetime = Field(..., description="Incident creation timestamp")


class IncidentUpdate(BaseModel):
    """Schema for updating incidents"""
    last_status: Optional[IncidentStatus] = Field(None, description="Updated incident status")
    location: Optional[LocationData] = Field(None, description="Updated location")
    score_band: Optional[ScoreBand] = Field(None, description="Updated score band")
    details: Optional[str] = Field(None, description="Updated details")
    fir_pdf_path: Optional[str] = Field(None, description="Generated FIR PDF path")


class IncidentResponse(IncidentBase):
    """Schema for incident API responses"""
    alert_id: int = Field(..., description="Unique alert identifier")
    created_at: datetime = Field(..., description="Incident creation timestamp")
    last_status: IncidentStatus = Field(..., description="Current incident status")
    last_update_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class IncidentSummary(BaseModel):
    """Lightweight incident summary for lists"""
    alert_id: int
    type: IncidentType
    last_status: IncidentStatus
    created_at: datetime
    score_band: Optional[ScoreBand] = None
    tourist_id: Optional[str] = None
    location: Optional[LocationData] = None
    fir_pdf_path: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# Action Schemas
class ActionBase(BaseModel):
    """Base action schema"""
    officer_id: str = Field(..., description="Police officer identifier")
    action: ActionType = Field(..., description="Type of action performed")
    note: Optional[str] = Field(None, description="Optional action note")


class ActionCreate(ActionBase):
    """Schema for creating actions"""
    alert_id: int = Field(..., description="Associated incident alert ID")


class ActionResponse(ActionBase):
    """Schema for action API responses"""
    id: int = Field(..., description="Unique action identifier")
    alert_id: int = Field(..., description="Associated incident alert ID")
    performed_at: datetime = Field(..., description="Action timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# ACK Request Schema
class AckRequest(BaseModel):
    """Schema for incident acknowledgment requests"""
    alert_id: int = Field(..., description="Incident alert ID to acknowledge")
    tourist_id: str = Field(..., description="Tourist ID for verification")
    note: str = Field(..., description="ACK note/reason")
    officer_id: str = Field(..., description="Acknowledging officer ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "alert_id": 987654,
                "tourist_id": "b1d0b691-1234-5678-9abc-123456789012",
                "note": "Unit dispatched to location",
                "officer_id": "ps-12-ajay"
            }
        }
    )


class AckResponse(BaseModel):
    """Schema for ACK response"""
    success: bool = Field(..., description="Whether ACK was successful")
    message: str = Field(..., description="Response message")
    action_id: Optional[int] = Field(None, description="Created action ID")
    timestamp: datetime = Field(..., description="ACK timestamp")


# Setting Schemas
class SettingBase(BaseModel):
    """Base setting schema"""
    key: str = Field(..., description="Setting key")
    value: Optional[str] = Field(None, description="Setting value")


class SettingCreate(SettingBase):
    """Schema for creating settings"""
    pass


class SettingUpdate(BaseModel):
    """Schema for updating settings"""
    value: str = Field(..., description="New setting value")


class SettingResponse(SettingBase):
    """Schema for setting API responses"""
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# Filter and Query Schemas
class IncidentFilters(BaseModel):
    """Schema for incident filtering and search"""
    type: Optional[IncidentType] = Field(None, description="Filter by incident type")
    status: Optional[IncidentStatus] = Field(None, description="Filter by status")
    score_band: Optional[ScoreBand] = Field(None, description="Filter by score band")
    from_date: Optional[datetime] = Field(None, description="Filter incidents from this date")
    to_date: Optional[datetime] = Field(None, description="Filter incidents to this date")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = ['created_at', 'last_update_at', 'type', 'last_status', 'alert_id']
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of: {allowed_fields}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v.lower()


# Dashboard and Statistics Schemas
class IncidentStats(BaseModel):
    """Schema for incident statistics"""
    total_incidents: int = Field(..., description="Total number of incidents")
    active_incidents: int = Field(..., description="Number of active incidents")
    acknowledged_incidents: int = Field(..., description="Number of acknowledged incidents")
    resolved_incidents: int = Field(..., description="Number of resolved incidents")
    by_type: Dict[str, int] = Field(..., description="Incident count by type")
    by_score_band: Dict[str, int] = Field(..., description="Incident count by score band")
    recent_activity: int = Field(..., description="Incidents in last 24 hours")


class DashboardData(BaseModel):
    """Schema for dashboard data"""
    stats: IncidentStats = Field(..., description="Incident statistics")
    recent_incidents: List[IncidentSummary] = Field(..., description="Recent incidents")
    urgent_incidents: List[IncidentSummary] = Field(..., description="High priority incidents")
    last_updated: datetime = Field(..., description="Data last updated timestamp")
