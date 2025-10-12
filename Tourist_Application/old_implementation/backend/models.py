from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class PositionData(BaseModel):
    lat: float
    lng: float
    alt: Optional[float] = None
    speed_mps: Optional[float] = None
    ts: Optional[datetime] = None


class HealthData(BaseModel):
    heart_rate: Optional[int] = None
    fall_detected: Optional[bool] = None
    battery: Optional[float] = None


class AppMetadata(BaseModel):
    build: str
    platform: str


class LocationData(BaseModel):
    lat: float
    lng: float
    timestamp: Optional[datetime] = None


class SOSData(BaseModel):
    active: bool
    lat: Optional[float] = None
    lng: Optional[float] = None
    timestamp: Optional[datetime] = None


class IngestPayload(BaseModel):
    tourist_id: Optional[str] = None
    device_id: Optional[str] = None
    position: PositionData
    health: Optional[HealthData] = None
    sos: Optional[SOSData] = None
    app: AppMetadata


class DeviceRegistration(BaseModel):
    tourist_id: str
    device_id: str
    secret_hint: Optional[str] = None


class SimulationPath(BaseModel):
    name: str
    coordinates: List[List[float]]  # [[lat, lon], [lat, lon], ...]
    speed: float = 1.0  # points per second


class SimulationStatus(BaseModel):
    active: bool
    current_position: Optional[LocationData] = None
    path_name: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0


class AuthStatus(BaseModel):
    authenticated: bool
    token_expires: Optional[datetime] = None
    user_id: Optional[str] = None


class ConnectionStatus(BaseModel):
    gateway_connected: bool
    mqtt_connected: bool
    keycloak_connected: bool
    last_check: datetime


class AppStatus(BaseModel):
    auth: AuthStatus
    connection: ConnectionStatus
    simulation: SimulationStatus
    last_location: Optional[LocationData] = None
    last_sos: Optional[SOSData] = None
