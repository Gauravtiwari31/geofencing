"""
Incident service layer
Business logic for incident operations
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from models.models import Incident, Action, Setting
from models.schemas import (
    IncidentCreate, IncidentUpdate, IncidentFilters,
    IncidentResponse, IncidentSummary, IncidentStats,
    ActionCreate, AckRequest
)

logger = structlog.get_logger()


class IncidentService:
    """Service for incident-related database operations"""

    @staticmethod
    async def create_incident(db: AsyncSession, incident_data: IncidentCreate) -> Incident:
        """Create a new incident"""
        try:
            # Convert Pydantic model to dict, handling nested models
            incident_dict = incident_data.model_dump()
            
            # Handle location data conversion to JSON
            if incident_dict.get('location'):
                # Location is already a dict from Pydantic
                pass
            
            # Create incident
            incident = Incident(**incident_dict)
            db.add(incident)
            await db.flush()
            await db.refresh(incident)
            
            logger.info("Incident created", alert_id=incident.alert_id, type=incident.type)
            return incident
            
        except Exception as e:
            logger.error("Failed to create incident", error=str(e))
            raise


    @staticmethod
    async def get_incident(db: AsyncSession, alert_id: int) -> Optional[Incident]:
        """Get incident by alert_id"""
        try:
            query = select(Incident).options(selectinload(Incident.actions)).where(Incident.alert_id == alert_id)
            result = await db.execute(query)
            incident = result.scalar_one_or_none()
            
            if incident:
                logger.debug("Incident retrieved", alert_id=alert_id)
            
            return incident
            
        except Exception as e:
            logger.error("Failed to get incident", alert_id=alert_id, error=str(e))
            raise


    @staticmethod
    async def update_incident(db: AsyncSession, alert_id: int, update_data: IncidentUpdate) -> Optional[Incident]:
        """Update an incident"""
        try:
            incident = await IncidentService.get_incident(db, alert_id)
            if not incident:
                return None
            
            # Update fields that are provided
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(incident, field, value)
            
            incident.last_update_at = datetime.utcnow()
            await db.flush()
            await db.refresh(incident)
            
            logger.info("Incident updated", alert_id=alert_id, updates=list(update_dict.keys()))
            return incident
            
        except Exception as e:
            logger.error("Failed to update incident", alert_id=alert_id, error=str(e))
            raise


    @staticmethod
    async def list_incidents(db: AsyncSession, filters: IncidentFilters) -> Tuple[List[Incident], int]:
        """List incidents with filtering and pagination"""
        try:
            # Base query
            query = select(Incident)
            count_query = select(func.count(Incident.alert_id))
            
            # Apply filters
            conditions = []
            
            if filters.type:
                conditions.append(Incident.type == filters.type)
            
            if filters.status:
                conditions.append(Incident.last_status == filters.status)
            
            if filters.score_band:
                conditions.append(Incident.score_band == filters.score_band)
            
            if filters.from_date:
                conditions.append(Incident.created_at >= filters.from_date)
            
            if filters.to_date:
                conditions.append(Incident.created_at <= filters.to_date)
            
            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))
            
            # Get total count
            count_result = await db.execute(count_query)
            total_count = count_result.scalar()
            
            # Apply sorting
            sort_column = getattr(Incident, filters.sort_by)
            if filters.sort_order == 'desc':
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Apply pagination
            query = query.offset(filters.offset).limit(filters.limit)
            
            # Execute query
            result = await db.execute(query)
            incidents = result.scalars().all()
            
            logger.debug("Incidents listed", count=len(incidents), total=total_count, filters=filters.model_dump())
            return list(incidents), total_count
            
        except Exception as e:
            logger.error("Failed to list incidents", error=str(e))
            raise


    @staticmethod
    async def acknowledge_incident(db: AsyncSession, ack_request: AckRequest) -> Tuple[bool, str, Optional[int]]:
        """Acknowledge an incident and create action record"""
        try:
            # Get the incident
            incident = await IncidentService.get_incident(db, ack_request.alert_id)
            if not incident:
                return False, "Incident not found", None
            
            # Verify tourist_id matches
            if incident.tourist_id != ack_request.tourist_id:
                logger.warning("ACK request tourist_id mismatch", 
                             alert_id=ack_request.alert_id, 
                             expected=incident.tourist_id,
                             received=ack_request.tourist_id)
                return False, "Tourist ID mismatch", None
            
            # Check if already acknowledged
            if incident.last_status in ("ACKNOWLEDGED", "RESOLVED"):
                return False, f"Incident already {incident.last_status.lower()}", None
            
            # Update incident status
            incident.last_status = "ACKNOWLEDGED"
            incident.last_update_at = datetime.utcnow()
            
            # Create action record
            action = Action(
                alert_id=ack_request.alert_id,
                officer_id=ack_request.officer_id,
                action="ACK",
                note=ack_request.note,
                performed_at=datetime.utcnow()
            )
            db.add(action)
            
            await db.flush()
            await db.refresh(action)
            await db.commit()
            
            logger.info("Incident acknowledged", 
                       alert_id=ack_request.alert_id,
                       officer_id=ack_request.officer_id,
                       action_id=action.id)
            
            # Broadcast SSE event for real-time updates
            try:
                from services.sse_service import incident_broadcaster
                incident_dict = incident.to_dict()
                await incident_broadcaster.incident_acknowledged(
                    incident_dict,
                    ack_request.officer_id,
                    ack_request.note
                )
            except Exception as e:
                # Don't fail the operation if SSE broadcast fails
                logger.warning("Failed to broadcast SSE event", error=str(e))

            # Forward acknowledgement to MoD Core (best-effort)
            try:
                from services.mod_core_client import mod_core_client

                await mod_core_client.send_acknowledgement(
                    alert_id=ack_request.alert_id,
                    tourist_id=ack_request.tourist_id,
                    officer_id=ack_request.officer_id,
                    note=ack_request.note,
                )
            except Exception as e:
                logger.warning(
                    "Failed to forward acknowledgement to MoD Core",
                    alert_id=ack_request.alert_id,
                    error=str(e),
                )
            
            return True, "Incident acknowledged successfully", action.id
            
        except Exception as e:
            logger.error("Failed to acknowledge incident", alert_id=ack_request.alert_id, error=str(e))
            raise


    @staticmethod
    async def create_action(db: AsyncSession, action_data: ActionCreate) -> Optional[Action]:
        """Create an action record"""
        try:
            # Verify incident exists
            incident = await IncidentService.get_incident(db, action_data.alert_id)
            if not incident:
                logger.warning("Cannot create action for non-existent incident", alert_id=action_data.alert_id)
                return None
            
            action = Action(**action_data.model_dump(), performed_at=datetime.utcnow())
            db.add(action)
            await db.flush()
            await db.refresh(action)
            
            logger.info("Action created", action_id=action.id, type=action.action, alert_id=action.alert_id)
            return action
            
        except Exception as e:
            logger.error("Failed to create action", error=str(e))
            raise


    @staticmethod
    async def get_incident_statistics(db: AsyncSession) -> IncidentStats:
        """Get incident statistics for dashboard"""
        try:
            # Total incidents
            total_query = select(func.count(Incident.alert_id))
            total_result = await db.execute(total_query)
            total_incidents = total_result.scalar()
            
            # Status counts
            status_query = select(Incident.last_status, func.count(Incident.alert_id)).group_by(Incident.last_status)
            status_result = await db.execute(status_query)
            status_counts = dict(status_result.all())
            
            # Type counts
            type_query = select(Incident.type, func.count(Incident.alert_id)).group_by(Incident.type)
            type_result = await db.execute(type_query)
            type_counts = dict(type_result.all())
            
            # Score band counts
            band_query = select(Incident.score_band, func.count(Incident.alert_id)).group_by(Incident.score_band)
            band_result = await db.execute(band_query)
            band_counts = dict(band_result.all())
            
            # Recent activity (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_query = select(func.count(Incident.alert_id)).where(Incident.created_at >= recent_cutoff)
            recent_result = await db.execute(recent_query)
            recent_activity = recent_result.scalar()
            
            stats = IncidentStats(
                total_incidents=total_incidents,
                active_incidents=status_counts.get("ACTIVE", 0),
                acknowledged_incidents=status_counts.get("ACKNOWLEDGED", 0),
                resolved_incidents=status_counts.get("RESOLVED", 0),
                by_type=type_counts,
                by_score_band={k: v for k, v in band_counts.items() if k is not None},
                recent_activity=recent_activity
            )
            
            logger.debug("Statistics generated", total=total_incidents, active=stats.active_incidents)
            return stats
            
        except Exception as e:
            logger.error("Failed to get incident statistics", error=str(e))
            raise


    @staticmethod
    async def get_urgent_incidents(db: AsyncSession, limit: int = 10) -> List[Incident]:
        """Get most urgent active incidents"""
        try:
            # Get active incidents with high priority
            query = (select(Incident)
                    .where(Incident.last_status == "ACTIVE")
                    .where(or_(
                        Incident.type == "SOS",
                        Incident.score_band == "HIGH"
                    ))
                    .order_by(desc(Incident.created_at))
                    .limit(limit))
            
            result = await db.execute(query)
            incidents = result.scalars().all()
            
            logger.debug("Urgent incidents retrieved", count=len(incidents))
            return list(incidents)
            
        except Exception as e:
            logger.error("Failed to get urgent incidents", error=str(e))
            raise
