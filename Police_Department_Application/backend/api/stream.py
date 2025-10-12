"""
SSE Streaming API Endpoints
Real-time Server-Sent Events for live incident updates
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from sse_starlette import EventSourceResponse
import structlog

from services.sse_service import sse_manager, incident_broadcaster

logger = structlog.get_logger()
router = APIRouter()


@router.get("/stream")
async def incident_stream(
    request: Request,
    client_id: Optional[str] = None,
):
    """
    Server-Sent Events stream for real-time incident updates
    
    Provides live updates for:
    - New incidents
    - Incident status changes
    - Acknowledgments
    - Statistics updates
    """
    # Generate client ID if not provided
    if not client_id:
        client_id = f"client_{uuid.uuid4().hex[:8]}"
    
    logger.info(
        "Starting SSE stream",
        client_id=client_id,
        user_agent=request.headers.get("user-agent", "unknown"),
    )
    
    try:
        # Add client to SSE manager
        queue = await sse_manager.add_client(client_id, request)
        
        # Create the event generator
        async def event_generator():
            try:
                async for event in sse_manager.get_client_generator(client_id):
                    yield event
            except Exception as e:
                logger.error("SSE stream error", 
                           client_id=client_id, 
                           error=str(e))
                # Send error event before closing
                yield {
                    "event": "error",
                    "data": f'{{"type": "error", "message": "Stream error: {str(e)}", "timestamp": "{str(e)}"}}'
                }
        
        # Return EventSourceResponse
        return EventSourceResponse(
            event_generator(),
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error("Failed to start SSE stream", 
                    client_id=client_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to establish event stream"
        )


@router.post("/broadcast/test")
async def test_broadcast(
    message: str = "Test broadcast message",
):
    """
    Test endpoint to broadcast a message to all connected clients
    Useful for testing SSE functionality
    """
    try:
        await incident_broadcaster.system_status(
            status="info",
            message=f"Test message: {message}"
        )
        
        stats = sse_manager.get_connection_stats()
        
        return JSONResponse(
            content={
                "success": True,
                "message": "Test broadcast sent",
                "recipients": stats["total_connections"],
                "timestamp": "now"
            }
        )
        
    except Exception as e:
        logger.error("Test broadcast failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test broadcast"
        )


@router.get("/connections")
async def get_connection_stats():
    """
    Get statistics about current SSE connections
    Useful for monitoring and debugging
    """
    try:
        stats = sse_manager.get_connection_stats()
        
        return JSONResponse(
            content={
                "success": True,
                "data": stats,
                "timestamp": "now"
            }
        )
        
    except Exception as e:
        logger.error("Failed to get connection stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connection statistics"
        )


@router.post("/incident/{alert_id}/notify")
async def notify_incident_update(
    alert_id: int,
    event_type: str = "updated",
    message: Optional[str] = None,
):
    """
    Manually trigger a notification for an incident update
    Useful for testing or manual notifications
    """
    try:
        # In a real implementation, we'd fetch the incident from the database
        incident_data = {
            "alert_id": alert_id,
            "type": "MANUAL",
            "last_status": "UPDATED",
            "updated_by": current_user.user_id
        }
        
        if event_type == "acknowledged":
            await incident_broadcaster.incident_acknowledged(
                incident_data, 
                current_user.user_id,
                message or f"Manual notification by {current_user.username}"
            )
        elif event_type == "updated":
            await incident_broadcaster.incident_updated(
                incident_data,
                {"manually_updated": True}
            )
        else:
            await incident_broadcaster.system_status(
                status="info",
                message=message or f"Manual notification for incident #{alert_id}"
            )
        
        stats = sse_manager.get_connection_stats()
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"Notification sent for incident #{alert_id}",
                "event_type": event_type,
                "recipients": stats["total_connections"]
            }
        )
        
    except Exception as e:
        logger.error("Manual notification failed", 
                    alert_id=alert_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send manual notification"
        )
