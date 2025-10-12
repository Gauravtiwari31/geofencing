"""
Incidents API endpoints
REST API for incident management operations
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from models.database import get_db
from models.schemas import (
    IncidentResponse, IncidentSummary, IncidentFilters, IncidentStats,
    AckRequest, AckResponse, ActionResponse, DashboardData,
    IncidentType, IncidentStatus, ScoreBand
)
from services.incident_service import IncidentService
from services.fir_service import get_fir_file

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=List[IncidentSummary])
async def list_incidents(
    # Query parameters for filtering
    incident_type: Optional[IncidentType] = Query(None, description="Filter by incident type"),
    status: Optional[IncidentStatus] = Query(None, description="Filter by incident status"),
    score_band: Optional[ScoreBand] = Query(None, description="Filter by score band"),
    from_date: Optional[datetime] = Query(None, description="Filter incidents from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter incidents to this date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of incidents with filtering and pagination
    
    Returns a paginated list of incidents based on the provided filters.
    Supports sorting and limiting results for performance.
    """
    try:
        # Create filters object
        filters = IncidentFilters(
            type=incident_type,
            status=status,
            score_band=score_band,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get incidents
        incidents, total_count = await IncidentService.list_incidents(db, filters)
        
        # Convert to summary format for list view
        incident_summaries = [
            IncidentSummary(
                alert_id=incident.alert_id,
                type=incident.type,
            last_status=incident.last_status,
                created_at=incident.created_at,
                score_band=incident.score_band,
                tourist_id=incident.tourist_id,
                location=incident.location,
                fir_pdf_path=incident.fir_download_url(),
            )
            for incident in incidents
        ]
        
        logger.info("Incidents listed", count=len(incident_summaries), total=total_count, filters=filters.model_dump())
        
        # Return the summaries directly (FastAPI will handle JSON conversion)
        return incident_summaries
        
    except Exception as e:
        logger.error("Failed to list incidents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve incidents"
        )


@router.get("/urgent", response_model=List[IncidentSummary])
async def get_urgent_incidents(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of urgent incidents"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get urgent incidents requiring immediate attention
    
    Returns active incidents with high priority (SOS alerts and HIGH score band).
    """
    try:
        urgent_incidents = await IncidentService.get_urgent_incidents(db, limit=limit)
        
        urgent_summaries = [
            IncidentSummary(
                alert_id=incident.alert_id,
                type=incident.type,
                last_status=incident.last_status,
                created_at=incident.created_at,
                score_band=incident.score_band,
                tourist_id=incident.tourist_id,
                location=incident.location,
                fir_pdf_path=incident.fir_download_url(),
            )
            for incident in urgent_incidents
        ]
        
        logger.info("Urgent incidents retrieved", count=len(urgent_summaries))
        return urgent_summaries
        
    except Exception as e:
        logger.error("Failed to get urgent incidents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve urgent incidents"
        )


@router.get("/{alert_id}", response_model=IncidentResponse)
async def get_incident(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific incident
    
    Returns complete incident details including location data and action history.
    """
    try:
        incident = await IncidentService.get_incident(db, alert_id)
        
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with alert_id {alert_id} not found"
            )
        
        # Convert to response format
        incident_response = IncidentResponse(
            alert_id=incident.alert_id,
            tourist_id=incident.tourist_id,
            type=incident.type,
            created_at=incident.created_at,
            last_status=incident.last_status,
            last_update_at=incident.last_update_at,
            location=incident.location,
            score_band=incident.score_band,
            details=incident.details,
            fir_pdf_path=incident.fir_download_url(),
        )
        
        logger.info("Incident retrieved", alert_id=alert_id, type=incident.type)
        return incident_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get incident", alert_id=alert_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve incident"
        )


@router.post("/{alert_id}/ack", response_model=AckResponse)
async def acknowledge_incident(
    alert_id: int,
    ack_request: AckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledge an incident
    
    Records that a police officer has acknowledged and is responding to an incident.
    This will update the incident status and create an audit log entry.
    """
    try:
        # Verify alert_id matches request body
        if ack_request.alert_id != alert_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alert ID in URL does not match request body"
            )
        
        # Process acknowledgment
        success, message, action_id = await IncidentService.acknowledge_incident(db, ack_request)
        
        if not success:
            # Determine appropriate error status
            if "not found" in message.lower():
                status_code = status.HTTP_404_NOT_FOUND
            elif "mismatch" in message.lower():
                status_code = status.HTTP_400_BAD_REQUEST
            else:
                status_code = status.HTTP_409_CONFLICT
                
            raise HTTPException(status_code=status_code, detail=message)
        
        # Create successful response
        response = AckResponse(
            success=True,
            message=message,
            action_id=action_id,
            timestamp=datetime.utcnow()
        )
        
        logger.info("Incident acknowledged", 
                   alert_id=alert_id, 
                   officer_id=ack_request.officer_id,
                   action_id=action_id)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to acknowledge incident", alert_id=alert_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge incident"
        )


@router.get("/{alert_id}/actions", response_model=List[ActionResponse])
async def get_incident_actions(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get action history for an incident
    
    Returns all police actions performed on this incident for audit purposes.
    """
    try:
        incident = await IncidentService.get_incident(db, alert_id)
        
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with alert_id {alert_id} not found"
            )
        
        # Convert actions to response format
        action_responses = [
            ActionResponse(
                id=action.id,
                alert_id=action.alert_id,
                officer_id=action.officer_id,
                action=action.action,
                performed_at=action.performed_at,
                note=action.note
            )
            for action in incident.actions
        ]
        
        logger.info("Incident actions retrieved", alert_id=alert_id, count=len(action_responses))
        return action_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get incident actions", alert_id=alert_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve incident actions"
        )


@router.get("/stats/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard data including statistics and recent incidents
    
    Returns comprehensive data for the police dashboard including:
    - Overall incident statistics
    - Recent incidents
    - High priority active incidents
    """
    try:
        # Get statistics
        stats = await IncidentService.get_incident_statistics(db)
        
        # Get recent incidents (last 20)
        recent_filters = IncidentFilters(
            limit=20,
            sort_by="created_at",
            sort_order="desc"
        )
        recent_incidents, _ = await IncidentService.list_incidents(db, recent_filters)
        
        # Get urgent incidents
        urgent_incidents = await IncidentService.get_urgent_incidents(db, limit=10)
        
        # Convert to summary format
        recent_summaries = [
            IncidentSummary(
                alert_id=incident.alert_id,
                type=incident.type,
                last_status=incident.last_status,
                created_at=incident.created_at,
                score_band=incident.score_band,
                tourist_id=incident.tourist_id,
                location=incident.location,
                fir_pdf_path=incident.fir_download_url(),
            )
            for incident in recent_incidents
        ]
        
        urgent_summaries = [
            IncidentSummary(
                alert_id=incident.alert_id,
                type=incident.type,
                last_status=incident.last_status,
                created_at=incident.created_at,
                score_band=incident.score_band,
                tourist_id=incident.tourist_id,
                location=incident.location,
                fir_pdf_path=incident.fir_download_url(),
            )
            for incident in urgent_incidents
        ]
        
        dashboard_data = DashboardData(
            stats=stats,
            recent_incidents=recent_summaries,
            urgent_incidents=urgent_summaries,
            last_updated=datetime.utcnow()
        )
        
        logger.info("Dashboard data generated", 
                   total_incidents=stats.total_incidents,
                   active=stats.active_incidents,
                   recent_count=len(recent_summaries),
                   urgent_count=len(urgent_summaries))
        
        return dashboard_data
        
    except Exception as e:
        logger.error("Failed to get dashboard data", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )


@router.get("/stats/summary", response_model=IncidentStats)
async def get_incident_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get incident statistics summary
    
    Returns aggregated statistics about incidents for reporting and monitoring.
    """
    try:
        stats = await IncidentService.get_incident_statistics(db)
        
        logger.info("Statistics retrieved", 
                   total=stats.total_incidents,
                   active=stats.active_incidents)
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get incident statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.get("/urgent", response_model=List[IncidentSummary])
async def get_urgent_incidents(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of urgent incidents"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get urgent incidents requiring immediate attention
    
    Returns active incidents with high priority (SOS alerts and HIGH score band).
    """
    try:
        urgent_incidents = await IncidentService.get_urgent_incidents(db, limit=limit)
        
        urgent_summaries = [
            IncidentSummary(
                alert_id=incident.alert_id,
                type=incident.type,
                last_status=incident.last_status,
                created_at=incident.created_at,
                score_band=incident.score_band
            )
            for incident in urgent_incidents
        ]
        
        logger.info("Urgent incidents retrieved", count=len(urgent_summaries))
        return urgent_summaries
        
    except Exception as e:
        logger.error("Failed to get urgent incidents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve urgent incidents"
        )


@router.get("/{alert_id}/fir")
async def download_fir(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Download the generated FIR PDF for an incident."""
    incident = await IncidentService.get_incident(db, alert_id)
    if not incident or not incident.fir_pdf_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FIR PDF not available")

    absolute_path = get_fir_file(incident.fir_pdf_path)
    if not absolute_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FIR PDF file missing")

    return FileResponse(
        absolute_path,
        media_type="application/pdf",
        filename=f"fir_{incident.alert_id}.pdf"
    )
