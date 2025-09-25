"""
Police SEDI Main Application
FastAPI backend serving REST API and static frontend files
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import structlog

from config import settings
from api.health import router as health_router
from services import mod_core_client


# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("🚔 Starting Police SEDI Application")
    logger.info(f"📊 Database URL: {settings.database_url}")
    logger.info(f"🔐 OIDC Issuer: {settings.oidc_issuer_url}")
    logger.info(f"🌐 MoD Core URL: {settings.mod_core_url}")
    logger.info(f"🖥️  Serving on: {settings.host}:{settings.port}")
    
    # Initialize database
    try:
        from models.database import init_db
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error("❌ Database initialization failed", error=str(e))
        # Continue startup but mark as degraded
    
    # Start MoD Core SSE stream consumer
    try:
        await mod_core_client.start()
        logger.info("📡 MoD Core stream consumer started")
    except Exception as e:
        logger.error("❌ Failed to start MoD Core stream consumer", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Police SEDI Application")
    try:
        from models.database import close_db
        await close_db()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error("❌ Error closing database", error=str(e))
    # Stop MoD Core stream
    try:
        await mod_core_client.stop()
        logger.info("📡 MoD Core stream consumer stopped")
    except Exception as e:
        logger.error("❌ Error stopping MoD Core stream consumer", error=str(e))


# Create FastAPI application
app = FastAPI(
    title="Police SEDI API",
    description="Security & Emergency Data Interface - Real-time incident monitoring for police operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", f"https://localhost:{settings.port}"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router, tags=["System"])

# Import and include all API routers
from api.auth import router as auth_router
from api.incidents import router as incidents_router
from api.settings import router as settings_router
from api.stream import router as stream_router

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(incidents_router, prefix="/api/v1/incidents", tags=["Incidents"])
app.include_router(settings_router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(stream_router, prefix="/api/v1", tags=["Real-time"])


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """
    Serve the React frontend SPA
    In production, this serves the built React app
    In development, this provides a simple landing page
    """
    try:
        static_dir = Path(settings.static_directory)
        index_file = static_dir / "index.html"
        
        if index_file.exists():
            # Serve built React app
            return HTMLResponse(content=index_file.read_text(), status_code=200)
        else:
            # Development landing page
            return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Police SEDI - Development</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 40px; 
                    background: #f5f5f5; 
                }}
                .container {{ 
                    max-width: 800px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 40px; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .badge {{ 
                    display: inline-block; 
                    background: #007bff; 
                    color: white; 
                    padding: 4px 12px; 
                    border-radius: 4px; 
                    font-size: 0.9em; 
                    margin-left: 10px;
                }}
                .status {{ color: #28a745; font-weight: bold; }}
                .endpoint {{ 
                    background: #f8f9fa; 
                    padding: 8px 12px; 
                    border-radius: 4px; 
                    font-family: monospace; 
                    margin: 5px 0;
                }}
                ul {{ list-style-type: none; padding: 0; }}
                li {{ margin: 10px 0; }}
                .icon {{ margin-right: 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚔 Police SEDI Application</h1>
                <p class="status">✅ Backend is running successfully!</p>
                
                <h2>🔧 Development Mode</h2>
                <p>The React frontend is not built yet. Use the following endpoints:</p>
                
                <h3>📡 API Endpoints</h3>
                <ul>
                    <li><span class="icon">🏥</span><code class="endpoint">GET /health</code> - Health check</li>
                    <li><span class="icon">📚</span><code class="endpoint">GET /docs</code> - API Documentation (Swagger)</li>
                    <li><span class="icon">📖</span><code class="endpoint">GET /redoc</code> - API Documentation (ReDoc)</li>
                </ul>
                
                <h3>🚨 Incident Management</h3>
                <ul>
                    <li><span class="icon">📋</span><code class="endpoint">GET /api/v1/incidents</code> - List incidents</li>
                    <li><span class="icon">🔍</span><code class="endpoint">GET /api/v1/incidents/{{id}}</code> - Get incident details</li>
                    <li><span class="icon">✅</span><code class="endpoint">POST /api/v1/incidents/{{id}}/ack</code> - Acknowledge incident</li>
                    <li><span class="icon">📊</span><code class="endpoint">GET /api/v1/incidents/stats/dashboard</code> - Dashboard data</li>
                    <li><span class="icon">🚨</span><code class="endpoint">GET /api/v1/incidents/urgent</code> - Urgent incidents</li>
                </ul>
                
                <h3>🔐 Authentication</h3>
                <ul>
                    <li><span class="icon">👤</span><code class="endpoint">GET /auth/status</code> - Auth status</li>
                    <li><span class="icon">🔑</span><code class="endpoint">GET /auth/login</code> - Login</li>
                    <li><span class="icon">👋</span><code class="endpoint">POST /auth/logout</code> - Logout</li>
                    <li><span class="icon">ℹ️</span><code class="endpoint">GET /auth/user</code> - Current user info</li>
                </ul>
                
                <h3>🚀 Progress Status</h3>
                <ul>
                    <li><span class="icon">🗄️</span>Database Models <span class="badge" style="background: #28a745;">Complete</span></li>
                    <li><span class="icon">📡</span>REST API Endpoints <span class="badge" style="background: #28a745;">Complete</span></li>
                    <li><span class="icon">🔐</span>OIDC Authentication <span class="badge">Pending</span></li>
                    <li><span class="icon">📲</span>MoD Core Integration <span class="badge">Pending</span></li>
                    <li><span class="icon">🎨</span>React Frontend <span class="badge">Pending</span></li>
                    <li><span class="icon">📡</span>Real-time SSE <span class="badge">Pending</span></li>
                </ul>
                
                <h3>📊 System Information</h3>
                <ul>
                    <li><span class="icon">🐍</span>Python FastAPI Backend</li>
                    <li><span class="icon">🗄️</span>PostgreSQL Database (Port 2036)</li>
                    <li><span class="icon">🌐</span>Port: {settings.port}</li>
                    <li><span class="icon">🔧</span>Debug Mode: {settings.debug}</li>
                </ul>
            </div>
        </body>
        </html>
        """)
    except Exception as e:
        logger.error("Error serving frontend", error=str(e))
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html><head><title>Police SEDI - Error</title></head>
        <body><h1>Error loading page</h1><p>{str(e)}</p></body></html>
        """, status_code=500)


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors by serving the frontend for SPA routing"""
    return await serve_frontend()


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle internal server errors"""
    logger.error("Internal server error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please check the logs."
        }
    )


# Mount static files if they exist (for production)
static_dir = Path(settings.static_directory)
if static_dir.exists() and static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"📁 Mounted static files from {static_dir}")


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
