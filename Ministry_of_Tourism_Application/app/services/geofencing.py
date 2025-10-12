"""
Geofencing service for tourist safety monitoring
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, cast
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_Distance, ST_GeomFromText, ST_Within, ST_Contains

from app.models.geofence import Geofence, GeofenceEvent
from app.models.tourist import Tourist

logger = logging.getLogger(__name__)


def check_geofence_violations(
    db: Session, 
    latitude: float, 
    longitude: float,
    tourist_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Check if a location violates any active geofences.
    
    Args:
        db: Database session
        latitude: Location latitude
        longitude: Location longitude
        tourist_id: Optional tourist ID for logging events
    
    Returns:
        List of violation details
    """
    violations = []
    
    try:
        # Create point geometry
        point_wkt = f"POINT({longitude} {latitude})"
        
        # Query for geofences that contain this point
        violating_fences = db.query(Geofence).filter(
            Geofence.active == True,
            ST_Within(
                ST_GeomFromText(point_wkt, 4326),
                cast(Geofence.geom, Geometry("POLYGON", 4326))
            )
        ).all()
        
        for fence in violating_fences:
            violation = {
                "geofence_id": fence.id,
                "name": fence.name,
                "severity": fence.severity,
                "zone_type": fence.zone_type,
                "description": fence.description
            }
            violations.append(violation)
            
            # Log geofence event if tourist_id provided
            if tourist_id:
                log_geofence_event(
                    db, tourist_id, fence.id, "enter", latitude, longitude
                )
            
            logger.warning(
                f"Geofence violation: {fence.name} (severity {fence.severity}) "
                f"at {latitude}, {longitude}"
            )
        
        return violations
        
    except Exception as e:
        logger.error(f"Error checking geofence violations: {str(e)}")
        return []


def get_nearest_red_zone_distance(
    db: Session, 
    latitude: float, 
    longitude: float
) -> Optional[float]:
    """
    Get distance to nearest red zone in meters.
    
    Args:
        db: Database session
        latitude: Location latitude
        longitude: Location longitude
    
    Returns:
        Distance in meters, or None if no red zones found
    """
    try:
        # Create point geometry
        point_wkt = f"POINT({longitude} {latitude})"
        
        # First check if we're inside any red zone
        point_geom = ST_GeomFromText(point_wkt, 4326)

        inside_red_zone = db.query(Geofence).filter(
            Geofence.active == True,
            Geofence.zone_type == "red_zone",
            ST_Contains(cast(Geofence.geom, Geometry("POLYGON", 4326)), point_geom)
        ).first()
        
        if inside_red_zone:
            return 0.0  # Inside red zone
        
        # Find nearest red zone
        result = db.execute(text("""
            SELECT ST_Distance(
                ST_Transform(geom::geometry, 3857),
                ST_Transform(ST_GeomFromText(:point, 4326), 3857)
            ) as distance
            FROM geofences 
            WHERE active = true AND zone_type = 'red_zone'
            ORDER BY ST_Distance(
                ST_Transform(geom::geometry, 3857),
                ST_Transform(ST_GeomFromText(:point, 4326), 3857)
            )
            LIMIT 1
        """), {"point": point_wkt}).fetchone()
        
        if result:
            return float(result[0])
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting nearest red zone distance: {str(e)}")
        return None


def get_nearby_geofences(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float = 1000
) -> List[Dict[str, Any]]:
    """
    Get all geofences within specified radius.
    
    Args:
        db: Database session
        latitude: Location latitude
        longitude: Location longitude
        radius_meters: Search radius in meters
    
    Returns:
        List of nearby geofences with distances
    """
    try:
        point_wkt = f"POINT({longitude} {latitude})"
        
        # Query for nearby geofences
        result = db.execute(text("""
            SELECT 
                id, name, zone_type, severity, description,
                ST_Distance(
                    ST_Transform(geom::geometry, 3857),
                    ST_Transform(ST_GeomFromText(:point, 4326), 3857)
                ) as distance
            FROM geofences 
            WHERE active = true 
              AND ST_DWithin(
                    geom::geography,
                    ST_GeogFromText(:point),
                    :radius
              )
            ORDER BY distance
        """), {"point": point_wkt, "radius": radius_meters}).fetchall()
        
        geofences = []
        for row in result:
            geofences.append({
                "id": row[0],
                "name": row[1],
                "zone_type": row[2],
                "severity": row[3],
                "description": row[4],
                "distance_m": float(row[5])
            })
        
        return geofences
        
    except Exception as e:
        logger.error(f"Error getting nearby geofences: {str(e)}")
        return []


def log_geofence_event(
    db: Session,
    tourist_id: str,
    geofence_id: int,
    event_type: str,
    latitude: float,
    longitude: float,
    generate_alert: bool = True
) -> Optional[GeofenceEvent]:
    """
    Log a geofence entry/exit event.
    
    Args:
        db: Database session
        tourist_id: Tourist ID
        geofence_id: Geofence ID
        event_type: "enter" or "exit"
        latitude: Event latitude
        longitude: Event longitude
        generate_alert: Whether to generate alert for this event
    
    Returns:
        Created GeofenceEvent or None
    """
    try:
        point_wkt = f"POINT({longitude} {latitude})"
        
        event = GeofenceEvent(
            tourist_id=tourist_id,
            geofence_id=geofence_id,
            event_type=event_type,
            location=point_wkt,
            alert_generated=generate_alert,
            geofence_metadata={
                "coordinates": [latitude, longitude],
                "timestamp": "now"
            }
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        logger.info(
            f"Logged geofence event: tourist {tourist_id} {event_type} "
            f"geofence {geofence_id} at {latitude}, {longitude}"
        )
        
        return event
        
    except Exception as e:
        logger.error(f"Error logging geofence event: {str(e)}")
        return None


def create_geofence(
    db: Session,
    name: str,
    zone_type: str,
    severity: int,
    coordinates: List[List[float]],
    description: Optional[str] = None,
    created_by: Optional[str] = None
) -> Optional[Geofence]:
    """
    Create a new geofence from coordinates.
    
    Args:
        db: Database session
        name: Geofence name
        zone_type: Type of zone (red_zone, restricted, caution, etc.)
        severity: Severity level (1-10)
        coordinates: List of [lat, lon] coordinate pairs forming polygon
        description: Optional description
        created_by: User who created the geofence
    
    Returns:
        Created Geofence or None
    """
    try:
        # Convert coordinates to WKT polygon
        # Note: PostGIS expects lon, lat order (x, y)
        coord_pairs = [f"{coord[1]} {coord[0]}" for coord in coordinates]
        
        # Ensure polygon is closed
        if coord_pairs[0] != coord_pairs[-1]:
            coord_pairs.append(coord_pairs[0])
        
        polygon_wkt = f"POLYGON(({', '.join(coord_pairs)}))"
        
        geofence = Geofence(
            name=name,
            zone_type=zone_type,
            severity=severity,
            geom=polygon_wkt,
            description=description,
            created_by=created_by,
            geofence_metadata={
                "coordinate_count": len(coordinates),
                "created_from": "api"
            }
        )
        
        db.add(geofence)
        db.commit()
        db.refresh(geofence)
        
        logger.info(f"Created geofence: {name} ({zone_type}, severity {severity})")
        return geofence
        
    except Exception as e:
        logger.error(f"Error creating geofence: {str(e)}")
        return None


def validate_tourist_movement(
    db: Session,
    tourist_id: str,
    previous_lat: float,
    previous_lon: float,
    current_lat: float,
    current_lon: float,
    time_diff_seconds: float
) -> Dict[str, Any]:
    """
    Validate tourist movement for anomaly detection.
    
    Args:
        db: Database session
        tourist_id: Tourist ID
        previous_lat: Previous latitude
        previous_lon: Previous longitude
        current_lat: Current latitude
        current_lon: Current longitude
        time_diff_seconds: Time difference between positions
    
    Returns:
        Movement validation results
    """
    validation = {
        "valid": True,
        "anomalies": [],
        "distance_m": 0,
        "warnings": []
    }
    
    try:
        # Calculate distance
        prev_point = f"POINT({previous_lon} {previous_lat})"
        curr_point = f"POINT({current_lon} {current_lat})"
        
        result = db.execute(text("""
            SELECT ST_Distance(
                ST_Transform(ST_GeomFromText(:prev, 4326), 3857),
                ST_Transform(ST_GeomFromText(:curr, 4326), 3857)
            )
        """), {"prev": prev_point, "curr": curr_point}).fetchone()
        
        if result:
            distance_m = float(result[0])
            validation["distance_m"] = distance_m
            
            if time_diff_seconds > 0:
                # Speed estimation removed as it is no longer part of the plan
                pass
        
        # Check for geofence jumping (entering restricted area without passing through border)
        violations_prev = check_geofence_violations(db, previous_lat, previous_lon)
        violations_curr = check_geofence_violations(db, current_lat, current_lon)
        
        # If currently in red zone but wasn't before, check for boundary crossing
        prev_in_red = any(v["zone_type"] == "red_zone" for v in violations_prev)
        curr_in_red = any(v["zone_type"] == "red_zone" for v in violations_curr)
        
        if curr_in_red and not prev_in_red and validation["distance_m"] > 100:
            validation["warnings"].append("sudden_red_zone_entry")
            logger.warning(
                f"Sudden red zone entry for tourist {tourist_id}: "
                f"{validation['distance_m']:.1f}m movement"
            )
        
        return validation
        
    except Exception as e:
        logger.error(f"Error validating movement: {str(e)}")
        validation["valid"] = False
        validation["anomalies"].append("validation_error")
        return validation


def get_geofence_statistics(db: Session) -> Dict[str, Any]:
    """
    Get statistics about geofences and violations.
    
    Returns:
        Dictionary with geofence statistics
    """
    try:
        stats = {
            "total_geofences": 0,
            "active_geofences": 0,
            "by_zone_type": {},
            "by_severity": {},
            "recent_violations": 0
        }
        
        # Total and active geofences
        stats["total_geofences"] = db.query(Geofence).count()
        stats["active_geofences"] = db.query(Geofence).filter(
            Geofence.active == True
        ).count()
        
        # By zone type
        zone_types = db.execute(text("""
            SELECT zone_type, COUNT(*) 
            FROM geofences 
            WHERE active = true 
            GROUP BY zone_type
        """)).fetchall()
        
        for zone_type, count in zone_types:
            stats["by_zone_type"][zone_type] = count
        
        # By severity
        severities = db.execute(text("""
            SELECT severity, COUNT(*) 
            FROM geofences 
            WHERE active = true 
            GROUP BY severity 
            ORDER BY severity
        """)).fetchall()
        
        for severity, count in severities:
            stats["by_severity"][severity] = count
        
        # Recent violations (last 24 hours)
        stats["recent_violations"] = db.execute(text("""
            SELECT COUNT(*) 
            FROM geofence_events 
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            AND event_type = 'enter'
        """)).scalar() or 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting geofence statistics: {str(e)}")
        return {"error": str(e)}
