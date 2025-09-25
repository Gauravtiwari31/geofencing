"""
Health Check API Endpoints
System status and monitoring endpoints
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import structlog

from config import settings
from services.mod_core_client import mod_core_client

logger = structlog.get_logger()
router = APIRouter()


async def check_database() -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        import asyncpg
        
        # Parse database URL to extract connection parameters
        db_url = settings.database_url
        if db_url.startswith("postgresql+asyncpg://"):
            # Remove the +asyncpg part for direct asyncpg connection
            asyncpg_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        else:
            asyncpg_url = db_url
            
        # Test connection
        conn = await asyncpg.connect(asyncpg_url)
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        
        return {
            "status": "healthy" if result == 1 else "unhealthy",
            "response_time_ms": "< 100",  # This is a quick check
            "details": "PostgreSQL connection successful"
        }
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Unable to connect to PostgreSQL"
        }


async def check_certificates() -> Dict[str, Any]:
    """Check if required certificates exist"""
    try:
        cert_status = {}
        
        # Check client certificate
        if os.path.exists(settings.mod_client_cert_path):
            cert_status["client_cert"] = "present"
        else:
            cert_status["client_cert"] = "missing"
            
        # Check client private key
        if os.path.exists(settings.mod_client_key_path):
            cert_status["client_key"] = "present"
        else:
            cert_status["client_key"] = "missing"
            
        # Check CA certificate
        if os.path.exists(settings.mod_ca_cert_path):
            cert_status["ca_cert"] = "present"
        else:
            cert_status["ca_cert"] = "missing"
            
        all_present = all(status == "present" for status in cert_status.values())
        
        return {
            "status": "healthy" if all_present else "degraded",
            "certificates": cert_status,
            "details": "All certificates present" if all_present else "Some certificates missing"
        }
    except Exception as e:
        logger.error("Certificate check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Certificate validation failed"
        }


async def check_mod_core() -> Dict[str, Any]:
    """Check MoD Core connectivity (basic reachability)"""
    try:
        if not settings.mod_core_enabled:
            return {
                "status": "disabled",
                "details": "MoD Core integration disabled via configuration"
            }

        status = mod_core_client.health_status()
        state = status.get("state", "unknown")

        if state == "connected":
            overall_status = "healthy"
        elif state in {"initializing", "stopped"}:
            overall_status = "degraded"
        elif state == "disabled":
            overall_status = "disabled"
        else:
            overall_status = "degraded"

        return {
            "status": overall_status,
            "state": state,
            "last_event_received_at": status.get("last_event_received_at"),
            "last_successful_connect_at": status.get("last_successful_connect_at"),
            "last_error": status.get("last_error"),
            "last_error_at": status.get("last_error_at"),
            "active_alerts": status.get("active_alerts"),
            "totals": status.get("totals", {}),
        }
    except Exception as e:
        logger.error("MoD Core health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Unable to retrieve MoD Core client status"
        }


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Returns system status and component health
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    try:
        # Run all health checks concurrently
        db_health, cert_health, mod_health = await asyncio.gather(
            check_database(),
            check_certificates(),
            check_mod_core(),
            return_exceptions=True
        )
        
        # Handle any exceptions from health checks
        if isinstance(db_health, Exception):
            db_health = {"status": "unhealthy", "error": str(db_health)}
        if isinstance(cert_health, Exception):
            cert_health = {"status": "unhealthy", "error": str(cert_health)}
        if isinstance(mod_health, Exception):
            mod_health = {"status": "unhealthy", "error": str(mod_health)}
        
        # Determine overall status
        statuses = [db_health["status"], cert_health["status"], mod_health["status"]]
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        health_data = {
            "status": overall_status,
            "timestamp": timestamp,
            "version": "1.0.0",
            "environment": "development" if settings.debug else "production",
            "components": {
                "database": db_health,
                "certificates": cert_health,
                "mod_core": mod_health
            },
            "system": {
                "port": settings.port,
                "host": settings.host,
                "debug": settings.debug
            }
        }
        
        # Return appropriate HTTP status code
        status_code = 200 if overall_status == "healthy" else 503
        
        return JSONResponse(content=health_data, status_code=status_code)
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": timestamp,
                "error": str(e),
                "message": "Health check system failure"
            },
            status_code=503
        )


@router.get("/health/db")
async def database_health():
    """Database-specific health check"""
    db_health = await check_database()
    status_code = 200 if db_health["status"] == "healthy" else 503
    return JSONResponse(content=db_health, status_code=status_code)


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness probe for container orchestration
    Returns 200 if the service is ready to accept traffic
    """
    try:
        # Basic readiness checks
        db_health = await check_database()
        
        if db_health["status"] == "healthy":
            return JSONResponse(
                content={
                    "ready": True,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "ready": False,
                    "reason": "Database not ready",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                status_code=503
            )
    except Exception as e:
        return JSONResponse(
            content={
                "ready": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            status_code=503
        )


@router.get("/health/live")
async def liveness_check():
    """
    Liveness probe for container orchestration
    Returns 200 if the service is alive (basic functionality)
    """
    return JSONResponse(
        content={
            "alive": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime": "running"  # In a real app, calculate actual uptime
        },
        status_code=200
    )
