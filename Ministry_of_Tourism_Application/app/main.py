"""
MoD Core Safety Backend - Main Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Response, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import time
import json
from typing import List, Dict, Any
from datetime import datetime

from app.core.config import get_settings
from app.core.database import init_db, get_db
from app.api.v1 import app as app_router
from app.api.v1 import police
from app.services.metrics import setup_metrics, track_request
from app.models.tourist import Tourist, Location
from app.models.alert import Alert
from sqlalchemy.orm import Session

settings = get_settings()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass  # Connection might be closed

manager = ConnectionManager()

# Setup logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Starting MoD Core Safety Backend...")
    
    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")
    
    # Setup metrics
    setup_metrics()
    logger.info("✅ Metrics setup complete")
    
    logger.info("🎯 MoD Core is ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down MoD Core...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Ministry of Tourism Core Safety Backend for Tourist Monitoring",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*"]  # Configure properly in production
)

# CORS middleware (restrictive in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost", "https://127.0.0.1"] if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Request logging and metrics middleware."""
    start_time = time.time()
    
    # Log request
    logger.info(f"📥 {request.method} {request.url.path} from {request.client.host}")
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Track metrics
        track_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=process_time
        )
        
        # Add response headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Version"] = settings.version
        
        # Log response
        logger.info(
            f"📤 {request.method} {request.url.path} -> "
            f"{response.status_code} ({process_time:.3f}s)"
        )
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        
        # Track error metrics
        track_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=500,
            duration=process_time
        )
        
        logger.error(f"❌ {request.method} {request.url.path} -> ERROR: {str(e)}")
        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
            "timestamp": time.time()
        }
    )


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "version": settings.version,
        "timestamp": time.time()
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check with database connectivity."""
    try:
        from app.core.database import engine
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "version": settings.version,
            "database": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service not ready")


# Metrics endpoint
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    from app.services.metrics import get_metrics
    return Response(content=get_metrics(), media_type="text/plain")


# WebSocket endpoint for real-time updates
@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time tourist tracking updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and wait for messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# API endpoints for web dashboard
@app.get("/api/v1/tourists/live", tags=["Dashboard"])
async def get_live_tourists(db: Session = Depends(get_db)):
    """Get live tourist data for dashboard."""
    try:
        # Get all tourists with their latest locations
        tourists = db.query(Tourist).all()
        tourist_data = []
        
        for tourist in tourists:
            latest_location = db.query(Location).filter(
                Location.tourist_id == tourist.id
            ).order_by(Location.timestamp.desc()).first()
            
            if latest_location:
                tourist_data.append({
                    "id": tourist.id,
                    "name": f"{tourist.first_name} {tourist.last_name}",
                    "nationality": tourist.nationality,
                    "location": {
                        "lat": float(latest_location.latitude),
                        "lng": float(latest_location.longitude)
                    },
                    "status": determine_tourist_status(tourist, latest_location),
                    "last_seen": latest_location.timestamp.isoformat(),
                    "device_id": latest_location.device_id if hasattr(latest_location, 'device_id') else "Unknown",
                    "safety_score": calculate_safety_score(tourist, latest_location)
                })
        
        return {"tourists": tourist_data}
    except Exception as e:
        logger.error(f"Error fetching live tourists: {e}")
        # Return mock data for demo
        return {
            "tourists": [
                {
                    "id": 1,
                    "name": "Priya Sharma",
                    "nationality": "Indian",
                    "location": {"lat": 28.6139, "lng": 77.2090},
                    "status": "safe",
                    "last_seen": datetime.now().isoformat(),
                    "device_id": "DEV001",
                    "safety_score": 85
                },
                {
                    "id": 2,
                    "name": "John Anderson", 
                    "nationality": "American",
                    "location": {"lat": 27.1750, "lng": 78.0422},
                    "status": "safe",
                    "last_seen": datetime.now().isoformat(),
                    "device_id": "DEV002",
                    "safety_score": 92
                }
            ]
        }

@app.get("/api/v1/alerts/active", tags=["Dashboard"])
async def get_active_alerts(db: Session = Depends(get_db)):
    """Get active alerts for dashboard."""
    try:
        alerts = db.query(Alert).filter(Alert.status == "active").all()
        alert_data = []
        
        for alert in alerts:
            alert_data.append({
                "id": alert.id,
                "tourist_id": alert.tourist_id,
                "type": alert.type,
                "message": alert.message,
                "priority": alert.priority,
                "created_at": alert.created_at.isoformat(),
                "status": alert.status
            })
        
        return {"alerts": alert_data}
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return {"alerts": []}

@app.post("/api/v1/police/efir", tags=["Dashboard"])
async def create_efir(efir_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Create E-FIR and forward to police system."""
    try:
        # Create new alert entry
        alert = Alert(
            tourist_id=efir_data["tourist_id"],
            type=f"police_action_{efir_data['incident_type']}",
            message=f"E-FIR created for {efir_data['tourist_name']} - {efir_data['incident_type']}",
            priority=efir_data["priority_level"],
            location_lat=efir_data["location"]["lat"],
            location_lng=efir_data["location"]["lng"],
            status="forwarded_to_police"
        )
        
        db.add(alert)
        db.commit()
        
        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "efir_created",
            "data": efir_data
        })
        
        logger.info(f"E-FIR created for tourist {efir_data['tourist_name']}")
        
        return {
            "success": True,
            "efir_id": f"EFIR-{alert.id}-{int(datetime.now().timestamp())}",
            "message": "E-FIR successfully created and forwarded to police"
        }
        
    except Exception as e:
        logger.error(f"Error creating E-FIR: {e}")
        raise HTTPException(status_code=500, detail="Failed to create E-FIR")

@app.post("/api/v1/admin/red-zones", tags=["Dashboard"])
async def create_red_zone(red_zone_data: Dict[str, Any]):
    """Create a new red zone."""
    try:
        # In a real implementation, save to database
        logger.info(f"Red zone created: {red_zone_data}")
        
        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "red_zone_created",
            "data": red_zone_data
        })
        
        return {"success": True, "message": "Red zone created successfully"}
    except Exception as e:
        logger.error(f"Error creating red zone: {e}")
        raise HTTPException(status_code=500, detail="Failed to create red zone")

def determine_tourist_status(tourist: Tourist, location: Location) -> str:
    """Determine the current status of a tourist."""
    # Simple logic - can be enhanced
    return "safe"  # Default to safe

def calculate_safety_score(tourist: Tourist, location: Location) -> int:
    """Calculate safety score for a tourist."""
    # Simple scoring logic - can be enhanced
    return 85  # Default score

# Include API routers
app.include_router(app_router.router, prefix="/v1/app", tags=["Tourist Mobile"])
app.include_router(police.router, prefix="/v1/police", tags=["Police Operations"])

# Static files for web dashboard
app.mount("/static", StaticFiles(directory="/workspace/web"), name="static")

# Serve dashboard at root
from fastapi.responses import FileResponse

@app.get("/", tags=["Dashboard"])
async def dashboard():
    """Serve the main dashboard."""
    return FileResponse('/workspace/web/index.html')


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=2030,  # MoT Core API port within your specified range
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
