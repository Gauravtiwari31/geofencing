import asyncio
import json
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from backend.auth import keycloak_auth, get_current_user, token_storage
from backend.gateway import gateway_client
from backend.mqtt_client import mqtt_client
from backend.simulation import path_simulator, PREDEFINED_PATHS
from backend.models import (
    LocationData, SOSData, DeviceRegistration, SimulationPath,
    AuthStatus, ConnectionStatus, AppStatus, IngestPayload, PositionData, HealthData, AppMetadata
)
from config.settings import settings


# FastAPI app
app = FastAPI(
    title="Tourist Mobile Simulator",
    description="Tourist mobile application simulator for testing Gateway integration",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Templates
templates = Jinja2Templates(directory="frontend")

# Global state
current_token: Optional[str] = None
current_user_id: Optional[str] = None
last_ingest_payload: Optional[IngestPayload] = None


def _build_redirect_uri(request: Request) -> str:
    if settings.app_external_base_url:
        return f"{settings.app_external_base_url.rstrip('/')}/auth/callback"

    scheme = request.headers.get("x-forwarded-proto", request.url.scheme or "http")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if not host:
        host = f"{settings.app_host}:{settings.app_port}"

    return f"{scheme}://{host.rstrip('/')}/auth/callback"


# Request models
class LocationRequest(BaseModel):
    lat: float
    lng: float


class SOSRequest(BaseModel):
    lat: float
    lng: float


class SimulationRequest(BaseModel):
    path_name: str


# Routes

@app.get("/", response_class=HTMLResponse)
async def get_main_page(request: Request):
    """Serve main web application"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/auth/login")
async def login(request: Request):
    """Redirect to Keycloak login"""
    redirect_uri = _build_redirect_uri(request)
    auth_url = await keycloak_auth.get_auth_url(redirect_uri)
    return RedirectResponse(url=auth_url)


@app.get("/auth/callback")
async def auth_callback(request: Request, code: str, state: str):
    """Handle Keycloak callback with PKCE"""
    global current_token, current_user_id

    # If using frontend-driven PKCE, serve the SPA so the browser JS can exchange the code
    if settings.keycloak_frontend_flow:
        return templates.TemplateResponse("index.html", {"request": request})

    try:
        print(f"DEBUG: Callback received - code: {code[:20]}..., state: {state}")

        redirect_uri = _build_redirect_uri(request)
        print(f"DEBUG: Using redirect URI: {redirect_uri}")

        token_data = await keycloak_auth.exchange_code_for_token(code, redirect_uri, state)

        print(f"DEBUG: Token exchange successful, received token: {token_data['access_token'][:50]}...")

        current_token = token_data["access_token"]

        # Get user info
        user_info = await keycloak_auth.get_user_info(current_token)
        current_user_id = user_info.get("sub", "unknown")

        # Store token
        token_storage.store_token(current_user_id, token_data)

        print(f"DEBUG: Authentication successful for user: {current_user_id}")
        return RedirectResponse(url="/")

    except Exception as e:
        print(f"DEBUG: Callback exception: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {e}")


@app.get("/auth/test-callback")
async def test_callback():
    """Test endpoint to simulate Keycloak callback for debugging"""
    return {
        "message": "Test callback endpoint - use this to debug the authentication flow",
        "instructions": "To test the callback flow:",
        "step1": "Copy the authorization code from browser URL after Keycloak redirect",
        "step2": "Use curl to POST to /auth/callback with code and state parameters",
        "example": "curl 'http://localhost:2040/auth/callback?code=abc123&state=xyz456'"
    }


@app.post("/auth/refresh")
async def refresh_auth():
    """Refresh authentication token"""
    global current_token, current_user_id
    
    if not current_user_id:
        raise HTTPException(status_code=401, detail="No active session")
    
    token_data = token_storage.get_token(current_user_id)
    if not token_data or "refresh_token" not in token_data:
        raise HTTPException(status_code=401, detail="No refresh token available")
    
    try:
        new_token_data = await keycloak_auth.refresh_token(token_data["refresh_token"])
        current_token = new_token_data["access_token"]
        token_storage.store_token(current_user_id, new_token_data)
        
        return {"status": "success", "message": "Token refreshed"}
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {e}")


@app.get("/auth/status")
async def get_auth_status():
    """Get authentication status"""
    if current_token and current_user_id:
        try:
            await keycloak_auth.verify_token(current_token)
            return AuthStatus(
                authenticated=True,
                user_id=current_user_id,
                token_expires=datetime.utcnow()  # Simplified
            )
        except:
            pass
    
    return AuthStatus(authenticated=False)


@app.post("/api/location")
async def send_location(request: Request, location_req: LocationRequest):
    """Send location to Gateway"""
    global last_ingest_payload
    position_ts = datetime.utcnow()
    position = PositionData(
        lat=location_req.lat,
        lng=location_req.lng,
        ts=position_ts
    )
    health = HealthData()  # Placeholder, extend when collecting health metrics
    app_meta = AppMetadata(build=settings.app_build_version, platform=settings.app_platform)
    payload = IngestPayload(
        tourist_id=current_user_id,
        device_id=settings.device_id,
        position=position,
        health=health,
        sos=None,
        app=app_meta
    )
    last_ingest_payload = payload

    # Prefer Bearer token from request header; fallback to server-side session token
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    bearer_token = None
    if auth_header and auth_header.lower().startswith("bearer "):
        bearer_token = auth_header.split(" ", 1)[1].strip()

    token_to_use = bearer_token or current_token

    if token_to_use:
        try:
            result = await gateway_client.send_ingest(payload, token_to_use)
            if not settings.mod_core_enable_forwarding:
                result.setdefault("mod_core", {"status": "disabled", "message": "MoD Core forwarding disabled (set MOD_CORE_ENABLE_FORWARDING=true)"})
            return result
        except Exception as e:
            return {
                "status": "accepted_locally",
                "message": f"Location recorded locally. Gateway error: {str(e)}",
                "payload": payload.model_dump(exclude_none=True)
            }
    else:
        return {
            "status": "accepted_locally",
            "message": "Location recorded locally (no token)",
            "payload": payload.model_dump(exclude_none=True)
        }


@app.post("/api/sos")
async def send_sos(request: Request, sos_req: SOSRequest):
    """Send SOS alert"""
    global last_ingest_payload
    position_ts = datetime.utcnow()
    position = PositionData(
        lat=sos_req.lat,
        lng=sos_req.lng,
        ts=position_ts
    )
    health = HealthData()
    app_meta = AppMetadata(build=settings.app_build_version, platform=settings.app_platform)
    sos_data = SOSData(
        active=True,
        lat=sos_req.lat,
        lng=sos_req.lng,
        timestamp=position_ts
    )
    payload = IngestPayload(
        tourist_id=current_user_id,
        device_id=settings.device_id,
        position=position,
        health=health,
        sos=sos_data,
        app=app_meta
    )
    last_ingest_payload = payload

    gateway_result = None
    mqtt_result = False

    # Prefer Bearer token from request header; fallback to server-side session token
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    bearer_token = None
    if auth_header and auth_header.lower().startswith("bearer "):
        bearer_token = auth_header.split(" ", 1)[1].strip()

    token_to_use = bearer_token or current_token

    if token_to_use:
        try:
            gateway_result = await gateway_client.send_sos(payload, token_to_use)
            if not settings.mod_core_enable_forwarding and isinstance(gateway_result, dict):
                gateway_result.setdefault("mod_core", {"status": "disabled", "message": "MoD Core forwarding disabled (set MOD_CORE_ENABLE_FORWARDING=true)"})
        except Exception as e:
            gateway_result = {"error": str(e), "status": "gateway_unavailable"}
    else:
        gateway_result = {"status": "demo_mode", "message": "SOS recorded locally (no token)"}

    try:
        mqtt_result = await mqtt_client.publish_sos(LocationData(lat=sos_req.lat, lng=sos_req.lng))
    except Exception as e:
        print(f"MQTT SOS failed: {e}")

    return {
        "status": "sos_sent",
        "message": f"🚨 EMERGENCY ALERT ACTIVATED at {sos_req.lat:.6f}, {sos_req.lng:.6f}",
        "gateway_result": gateway_result,
        "mod_core_forwarded": gateway_result.get("mod_core") if isinstance(gateway_result, dict) else None,
        "mqtt_sent": mqtt_result,
        "payload": payload.model_dump(exclude_none=True)
    }


@app.get("/api/status")
async def get_app_status():
    """Get application status"""
    # Check connectivity
    gateway_connected = await gateway_client.check_connectivity()
    mqtt_connected = mqtt_client.is_connected()
    
    connection_status = ConnectionStatus(
        gateway_connected=gateway_connected,
        mqtt_connected=mqtt_connected,
        keycloak_connected=True,  # Simplified
        last_check=datetime.utcnow()
    )
    
    auth_status = await get_auth_status()
    simulation_status = path_simulator.get_status()
    
    return AppStatus(
        auth=auth_status,
        connection=connection_status,
        simulation=simulation_status
    )


@app.post("/api/simulate/start")
async def start_simulation(sim_req: SimulationRequest):
    """Start path simulation"""
    if not current_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if sim_req.path_name not in PREDEFINED_PATHS:
        raise HTTPException(status_code=400, detail=f"Unknown path: {sim_req.path_name}")
    
    path = PREDEFINED_PATHS[sim_req.path_name]
    success = await path_simulator.start_simulation(path, current_token)
    
    if success:
        return {"status": "success", "message": f"Started simulation: {path.name}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to start simulation")


@app.post("/api/simulate/stop")
async def stop_simulation():
    """Stop path simulation"""
    await path_simulator.stop_simulation()
    return {"status": "success", "message": "Simulation stopped"}


@app.get("/api/simulate/status")
async def get_simulation_status():
    """Get simulation status"""
    return path_simulator.get_status()


@app.get("/api/simulate/paths")
async def get_available_paths():
    """Get available simulation paths"""
    return {
        "paths": {
            name: {"name": path.name, "points": len(path.coordinates), "speed": path.speed}
            for name, path in PREDEFINED_PATHS.items()
        }
    }


@app.post("/api/device/register")
async def register_device():
    """Register simulated ESP32 device"""
    if not current_token or not current_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    registration = DeviceRegistration(
        tourist_id=current_user_id,
        device_id=settings.device_id,
        secret_hint="tourist-simulator"
    )
    
    try:
        result = await gateway_client.register_device(registration, current_token)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/device/status")
async def get_device_status():
    """Get device status"""
    return {
        "device_id": settings.device_id,
        "registered": True,  # Simplified
        "mqtt_connected": mqtt_client.is_connected()
    }


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    print(f"Starting Tourist Mobile Simulator on {settings.app_host}:{settings.app_port}")
    print(f"Gateway URL: {settings.gateway_url}")
    print(f"MQTT Broker: {settings.gateway_mqtt_host}:{settings.gateway_mqtt_port}")
    
    # Connect to MQTT broker
    mqtt_connected = await mqtt_client.connect()
    if mqtt_connected:
        print("Connected to MQTT broker")
    else:
        print("Warning: Failed to connect to MQTT broker")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    print("Shutting down Tourist Mobile Simulator")
    
    # Stop simulation
    await path_simulator.stop_simulation()
    
    # Disconnect MQTT
    await mqtt_client.disconnect()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
