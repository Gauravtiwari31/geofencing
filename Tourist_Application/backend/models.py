from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


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
    location: LocationData
    timestamp: str
    sos: Optional[SOSData] = None


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
