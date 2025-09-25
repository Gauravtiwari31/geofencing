"""
MoD Core Safety Backend - Main Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.config import get_settings
from app.core.database import init_db
from app.api.v1 import app as app_router
from app.api.v1 import police
from app.services.metrics import setup_metrics, track_request

settings = get_settings()

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


# Include API routers
app.include_router(app_router.router, prefix="/v1/app", tags=["Tourist Mobile"])
app.include_router(police.router, prefix="/v1/police", tags=["Police Operations"])

# Dashboard API
from app.api.v1 import dashboard
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])

# Static files for web dashboard
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve dashboard at root
from fastapi.responses import FileResponse

@app.get("/", tags=["Dashboard"])
async def dashboard():
    """Serve the main dashboard."""
    return FileResponse('static/index.html')


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=2030,  # MoT Core API port within your specified range
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
