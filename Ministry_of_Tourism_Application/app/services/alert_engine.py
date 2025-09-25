"""
Alert generation and management engine
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.alert import Alert, AlertAcknowledgment
from app.models.tourist import Tourist, Location
from app.services.metrics import track_alert_created, update_active_alerts
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class AlertEngine:
    """Alert generation and lifecycle management."""
    
    @staticmethod
    def create_alert(
        db: Session,
        tourist_id: str,
        alert_type: str,
        priority: str,
        title: str,
        description: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        location_lat: Optional[str] = None,
        location_lon: Optional[str] = None
    ) -> Optional[Alert]:
        """
        Create a new alert.
        
        Args:
            db: Database session
            tourist_id: Tourist ID
            alert_type: Type of alert (SOS, GEOFENCE, INACTIVITY, VITALS, DEVIATION)
            priority: Priority level (LOW, MEDIUM, HIGH, CRITICAL)
            title: Alert title
            description: Alert description
            payload: Additional alert data
            location_lat: Latitude string
            location_lon: Longitude string
        
        Returns:
            Created Alert or None
        """
        try:
            # Check for duplicate recent alerts
            recent_alert = db.query(Alert).filter(
                Alert.tourist_id == tourist_id,
                Alert.alert_type == alert_type,
                Alert.status.in_(["NEW", "ACK"]),
                Alert.created_at > datetime.utcnow() - timedelta(minutes=5)
            ).first()
            
            if recent_alert and alert_type != "SOS":
                logger.info(f"Suppressing duplicate {alert_type} alert for tourist {tourist_id}")
                return recent_alert
            
            alert = Alert(
                tourist_id=tourist_id,
                alert_type=alert_type,
                priority=priority,
                title=title,
                description=description,
                payload=payload or {},
                location_lat=location_lat,
                location_lon=location_lon,
                police_notified=(priority in ["HIGH", "CRITICAL"])
            )
            
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            # Track metrics
            track_alert_created(alert_type, priority)
            
            logger.info(
                f"Created {priority} {alert_type} alert {alert.id} for tourist {tourist_id}"
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            return None
    
    @staticmethod
    def process_sos_alert(
        db: Session,
        tourist_id: str,
        telemetry_data: Dict[str, Any]
    ) -> Optional[Alert]:
        """
        Process SOS alert - highest priority.
        
        Args:
            db: Database session
            tourist_id: Tourist ID
            telemetry_data: Tourist telemetry data
        
        Returns:
            Created Alert or None
        """
        try:
            position = telemetry_data.get("position", {})
            health = telemetry_data.get("health", {})
            
            payload = {
                "trigger_time": position.get("ts"),
                "location": {
                    "lat": position.get("lat"),
                    "lon": position.get("lon"),
                    "alt": position.get("alt")
                },
                "health_data": {
                    "heart_rate": health.get("heart_rate"),
                    "battery": health.get("battery")
                },
                "device_info": telemetry_data.get("app", {})
            }
            
            alert = AlertEngine.create_alert(
                db=db,
                tourist_id=tourist_id,
                alert_type="SOS",
                priority="CRITICAL",
                title="Emergency SOS Activated",
                description="Tourist has activated emergency SOS signal",
                payload=payload,
                location_lat=str(position.get("lat", "")),
                location_lon=str(position.get("lon", ""))
            )
            
            if alert:
                logger.critical(f"SOS ALERT: Tourist {tourist_id} activated emergency signal")
            
            return alert
            
        except Exception as e:
            logger.error(f"Error processing SOS alert: {str(e)}")
            return None
    
    @staticmethod
    def process_geofence_alert(
        db: Session,
        tourist_id: str,
        violations: List[Dict[str, Any]],
        telemetry_data: Dict[str, Any]
    ) -> List[Alert]:
        """
        Process geofence violation alerts.
        
        Args:
            db: Database session
            tourist_id: Tourist ID
            violations: List of geofence violations
            telemetry_data: Tourist telemetry data
        
        Returns:
            List of created alerts
        """
        alerts = []
        
        try:
            for violation in violations:
                severity = violation.get("severity", 1)
                zone_type = violation.get("zone_type", "unknown")
                
                # Determine priority based on zone type and severity
                if zone_type == "red_zone" or severity >= 8:
                    priority = "HIGH"
                elif severity >= 5:
                    priority = "MEDIUM"
                else:
                    priority = "LOW"
                
                position = telemetry_data.get("position", {})
                
                payload = {
                    "geofence_id": violation.get("geofence_id"),
                    "geofence_name": violation.get("name"),
                    "zone_type": zone_type,
                    "severity": severity,
                    "entry_time": position.get("ts"),
                    "location": {
                        "lat": position.get("lat"),
                        "lon": position.get("lon")
                    }
                }
                
                title = f"Geofence Violation: {violation.get('name', 'Unknown Area')}"
                description = f"Tourist entered {zone_type} area with severity level {severity}"
                
                alert = AlertEngine.create_alert(
                    db=db,
                    tourist_id=tourist_id,
                    alert_type="GEOFENCE",
                    priority=priority,
                    title=title,
                    description=description,
                    payload=payload,
                    location_lat=str(position.get("lat", "")),
                    location_lon=str(position.get("lon", ""))
                )
                
                if alert:
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error processing geofence alerts: {str(e)}")
            return []
    
    @staticmethod
    def process_vitals_alert(
        db: Session,
        tourist_id: str,
        health_data: Dict[str, Any],
        telemetry_data: Dict[str, Any]
    ) -> Optional[Alert]:
        """
        Process health vitals alerts.
        
        Args:
            db: Database session
            tourist_id: Tourist ID
            health_data: Health monitoring data
            telemetry_data: Tourist telemetry data
        
        Returns:
            Created Alert or None
        """
        try:
            alerts_needed = []
            
            # Fall detection
            if health_data.get("fall_detected", False):
                alerts_needed.append({
                    "type": "fall",
                    "priority": "HIGH",
                    "title": "Fall Detected",
                    "description": "Device detected a fall event"
                })
            
            # Heart rate anomalies
            heart_rate = health_data.get("heart_rate")
            if heart_rate:
                if heart_rate > 140:
                    alerts_needed.append({
                        "type": "high_hr",
                        "priority": "MEDIUM",
                        "title": "High Heart Rate",
                        "description": f"Heart rate elevated to {heart_rate} BPM"
                    })
                elif heart_rate < 45:
                    alerts_needed.append({
                        "type": "low_hr",
                        "priority": "MEDIUM",
                        "title": "Low Heart Rate",
                        "description": f"Heart rate dropped to {heart_rate} BPM"
                    })
            
            # Process the most severe alert
            if alerts_needed:
                most_severe = max(alerts_needed, key=lambda x: {
                    "HIGH": 3, "MEDIUM": 2, "LOW": 1
                }[x["priority"]])
                
                position = telemetry_data.get("position", {})
                
                payload = {
                    "vitals_type": most_severe["type"],
                    "heart_rate": heart_rate,
                    "fall_detected": health_data.get("fall_detected", False),
                    "detection_time": position.get("ts"),
                    "all_anomalies": [a["type"] for a in alerts_needed]
                }
                
                alert = AlertEngine.create_alert(
                    db=db,
                    tourist_id=tourist_id,
                    alert_type="VITALS",
                    priority=most_severe["priority"],
                    title=most_severe["title"],
                    description=most_severe["description"],
                    payload=payload,
                    location_lat=str(position.get("lat", "")),
                    location_lon=str(position.get("lon", ""))
                )
                
                return alert
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing vitals alert: {str(e)}")
            return None
    
    @staticmethod
    def check_inactivity_alerts(db: Session) -> List[Alert]:
        """
        Check for tourist inactivity and create alerts.
        
        Args:
            db: Database session
        
        Returns:
            List of created inactivity alerts
        """
        alerts = []
        
        try:
            # Find tourists with no recent activity
            cutoff_time = datetime.utcnow() - timedelta(
                minutes=settings.sos_max_response_time // 60 * 3  # 6 minutes default
            )
            
            inactive_tourists = db.execute("""
                SELECT DISTINCT t.id, t.emergency_contact, l.recorded_at, l.geom
                FROM tourists t
                LEFT JOIN locations l ON t.id = l.tourist_id
                WHERE l.recorded_at = (
                    SELECT MAX(recorded_at) 
                    FROM locations l2 
                    WHERE l2.tourist_id = t.id
                )
                AND l.recorded_at < :cutoff_time
                AND NOT EXISTS (
                    SELECT 1 FROM alerts a 
                    WHERE a.tourist_id = t.id 
                    AND a.alert_type = 'INACTIVITY'
                    AND a.status IN ('NEW', 'ACK')
                    AND a.created_at > :cutoff_time
                )
            """, {"cutoff_time": cutoff_time}).fetchall()
            
            for tourist_id, emergency_contact, last_seen, last_location in inactive_tourists:
                # Calculate inactivity duration
                inactivity_minutes = (datetime.utcnow() - last_seen).total_seconds() / 60
                
                # Determine priority based on inactivity duration
                if inactivity_minutes > 60:  # 1 hour
                    priority = "HIGH"
                elif inactivity_minutes > 30:  # 30 minutes
                    priority = "MEDIUM"
                else:
                    priority = "LOW"
                
                payload = {
                    "last_seen": last_seen.isoformat(),
                    "inactivity_minutes": int(inactivity_minutes),
                    "emergency_contact": emergency_contact,
                    "check_time": datetime.utcnow().isoformat()
                }
                
                alert = AlertEngine.create_alert(
                    db=db,
                    tourist_id=tourist_id,
                    alert_type="INACTIVITY",
                    priority=priority,
                    title="Tourist Inactivity Detected",
                    description=f"No activity for {int(inactivity_minutes)} minutes",
                    payload=payload
                )
                
                if alert:
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking inactivity alerts: {str(e)}")
            return []
    
    @staticmethod
    def acknowledge_alert(
        db: Session,
        alert_id: int,
        officer_id: str,
        note: Optional[str] = None,
        action_taken: Optional[str] = None
    ) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            db: Database session
            alert_id: Alert ID
            officer_id: Officer ID acknowledging the alert
            note: Optional note
            action_taken: Action taken description
        
        Returns:
            True if successful, False otherwise
        """
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                logger.error(f"Alert {alert_id} not found")
                return False
            
            if alert.status == "RESOLVED":
                logger.warning(f"Alert {alert_id} already resolved")
                return False
            
            # Update alert status
            alert.status = "ACK"
            alert.ack_at = datetime.utcnow()
            
            # Calculate response time for SOS alerts
            if alert.alert_type == "SOS" and alert.created_at:
                response_time = (datetime.utcnow() - alert.created_at).total_seconds()
                alert.response_time_seconds = int(response_time)
            
            # Create acknowledgment record
            ack = AlertAcknowledgment(
                alert_id=alert_id,
                officer_id=officer_id,
                note=note,
                action_taken=action_taken
            )
            
            db.add(ack)
            db.commit()
            
            logger.info(f"Alert {alert_id} acknowledged by officer {officer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert: {str(e)}")
            return False


def process_telemetry_for_alerts(
    db: Session,
    telemetry_data: Dict[str, Any],
    safety_data: Dict[str, Any]
):
    """
    Background task to process telemetry and generate alerts.
    
    Args:
        db: Database session
        telemetry_data: Tourist telemetry data
        safety_data: Calculated safety data
    """
    try:
        tourist_id = telemetry_data.get("tourist_id")
        if not tourist_id:
            return
        
        alerts_created = []
        
        # 1. Check for SOS
        sos_data = telemetry_data.get("sos", {})
        if sos_data.get("active", False):
            alert = AlertEngine.process_sos_alert(db, tourist_id, telemetry_data)
            if alert:
                alerts_created.append(alert)
        
        # 2. Check for geofence violations
        violations = safety_data.get("violations", [])
        if violations:
            geofence_alerts = AlertEngine.process_geofence_alert(
                db, tourist_id, violations, telemetry_data
            )
            alerts_created.extend(geofence_alerts)
        
        # 3. Check for health vitals issues
        health_data = telemetry_data.get("health", {})
        if health_data.get("fall_detected") or health_data.get("heart_rate"):
            vitals_alert = AlertEngine.process_vitals_alert(
                db, tourist_id, health_data, telemetry_data
            )
            if vitals_alert:
                alerts_created.append(vitals_alert)
        
        # Update active alerts metrics
        for alert_type in ["SOS", "GEOFENCE", "INACTIVITY", "VITALS", "DEVIATION"]:
            count = db.query(Alert).filter(
                Alert.alert_type == alert_type,
                Alert.status.in_(["NEW", "ACK"])
            ).count()
            update_active_alerts(alert_type.lower(), count)
        
        if alerts_created:
            logger.info(f"Generated {len(alerts_created)} alerts for tourist {tourist_id}")
        
    except Exception as e:
        logger.error(f"Error processing telemetry for alerts: {str(e)}")


def get_alert_statistics(db: Session) -> Dict[str, Any]:
    """
    Get alert statistics for monitoring.
    
    Args:
        db: Database session
    
    Returns:
        Alert statistics dictionary
    """
    try:
        stats = {
            "total_alerts": 0,
            "active_alerts": 0,
            "by_type": {},
            "by_priority": {},
            "by_status": {},
            "response_times": {},
            "recent_24h": 0
        }
        
        # Total alerts
        stats["total_alerts"] = db.query(Alert).count()
        
        # Active alerts
        stats["active_alerts"] = db.query(Alert).filter(
            Alert.status.in_(["NEW", "ACK"])
        ).count()
        
        # By type
        type_counts = db.execute("""
            SELECT alert_type, COUNT(*) 
            FROM alerts 
            WHERE status IN ('NEW', 'ACK')
            GROUP BY alert_type
        """).fetchall()
        
        for alert_type, count in type_counts:
            stats["by_type"][alert_type] = count
        
        # By priority
        priority_counts = db.execute("""
            SELECT priority, COUNT(*) 
            FROM alerts 
            WHERE status IN ('NEW', 'ACK')
            GROUP BY priority
        """).fetchall()
        
        for priority, count in priority_counts:
            stats["by_priority"][priority] = count
        
        # By status
        status_counts = db.execute("""
            SELECT status, COUNT(*) 
            FROM alerts 
            GROUP BY status
        """).fetchall()
        
        for status, count in status_counts:
            stats["by_status"][status] = count
        
        # Average response times for SOS alerts
        sos_response = db.execute("""
            SELECT AVG(response_time_seconds), COUNT(*)
            FROM alerts 
            WHERE alert_type = 'SOS' 
            AND response_time_seconds IS NOT NULL
        """).fetchone()
        
        if sos_response and sos_response[1] > 0:
            stats["response_times"]["sos_avg_seconds"] = float(sos_response[0])
            stats["response_times"]["sos_count"] = sos_response[1]
        
        # Recent alerts (24h)
        stats["recent_24h"] = db.execute("""
            SELECT COUNT(*) 
            FROM alerts 
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """).scalar() or 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {str(e)}")
        return {"error": str(e)}
