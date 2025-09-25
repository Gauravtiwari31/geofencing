"""
Local messaging and notification service
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.alert import Alert
from app.models.tourist import Tourist, Location
from app.services.metrics import track_stream_event

logger = logging.getLogger(__name__)


class NotificationService:
    """Local notification and messaging service."""
    
    def __init__(self):
        """Initialize notification service."""
        self.message_queue = []
        self.advisory_cache = {}
        self.active_notifications = {}
    
    async def generate_safety_advisories(self, db: Session) -> List[Dict[str, Any]]:
        """Generate contextual safety advisories for tourists."""
        try:
            advisories = []
            
            # Get tourists with recent locations
            recent_locations = db.execute("""
                SELECT DISTINCT ON (l.tourist_id) 
                    l.tourist_id, 
                    ST_Y(l.geom) as lat, 
                    ST_X(l.geom) as lon,
                    l.recorded_at,
                    l.location_metadata
                FROM locations l
                WHERE l.recorded_at > NOW() - INTERVAL '1 hour'
                ORDER BY l.tourist_id, l.recorded_at DESC
            """).fetchall()
            
            for location_data in recent_locations:
                tourist_id = location_data[0]
                lat = location_data[1]
                lon = location_data[2]
                metadata = location_data[4] or {}
                
                advisory = await self.generate_tourist_advisory(
                    db, tourist_id, lat, lon, metadata
                )
                
                if advisory:
                    advisories.append(advisory)
            
            return advisories
            
        except Exception as e:
            logger.error(f"Error generating safety advisories: {str(e)}")
            return []
    
    async def generate_tourist_advisory(
        self, 
        db: Session, 
        tourist_id: str, 
        lat: float, 
        lon: float, 
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate advisory for specific tourist."""
        try:
            messages = []
            priority = "LOW"
            
            # Check battery level
            battery = metadata.get("battery", 1.0)
            if battery < 0.15:
                messages.append("Critical battery level! Charge immediately.")
                priority = "HIGH"
            elif battery < 0.3:
                messages.append("Battery is getting low. Please charge soon.")
                priority = "MEDIUM"
            
            # Check for nearby geofences
            nearby_fences = db.execute("""
                SELECT name, zone_type, severity,
                       ST_Distance(
                           ST_Transform(geom, 3857),
                           ST_Transform(ST_GeomFromText(:point, 4326), 3857)
                       ) as distance
                FROM geofences 
                WHERE active = true 
                AND ST_DWithin(
                    ST_Transform(geom, 3857),
                    ST_Transform(ST_GeomFromText(:point, 4326), 3857),
                    1000
                )
                ORDER BY distance
                LIMIT 3
            """, {"point": f"POINT({lon} {lat})"}).fetchall()
            
            for fence in nearby_fences:
                name, zone_type, severity, distance = fence
                distance_m = int(distance)
                
                if zone_type == "red_zone" and distance_m < 500:
                    messages.append(f"Warning: Approaching restricted area '{name}' ({distance_m}m away)")
                    priority = "HIGH"
                elif zone_type == "caution" and distance_m < 300:
                    messages.append(f"Caution: Near construction area '{name}' ({distance_m}m away)")
                    if priority == "LOW":
                        priority = "MEDIUM"
            
            # Check weather/time-based advisories
            current_hour = datetime.utcnow().hour
            if current_hour >= 20 or current_hour <= 5:
                messages.append("It's nighttime. Stay in well-lit areas and avoid isolated locations.")
            
            # Check heart rate if available
            heart_rate = metadata.get("heart_rate")
            if heart_rate:
                if heart_rate > 120:
                    messages.append("Elevated heart rate detected. Take a break if needed.")
                    if priority == "LOW":
                        priority = "MEDIUM"
            
            # Check active alerts
            active_alerts = db.query(Alert).filter(
                Alert.tourist_id == tourist_id,
                Alert.status.in_(["NEW", "ACK"])
            ).count()
            
            if active_alerts > 0:
                messages.append("You have active safety alerts. Please check your app.")
                priority = "HIGH"
            
            if not messages:
                # Default positive message
                messages.append("You're in a safe area. Enjoy your visit!")
            
            return {
                "tourist_id": tourist_id,
                "messages": messages,
                "priority": priority,
                "location": {"lat": lat, "lon": lon},
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "battery": battery,
                    "nearby_zones": len(nearby_fences),
                    "active_alerts": active_alerts
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating tourist advisory: {str(e)}")
            return None
    
    async def check_notification_triggers(self, db: Session) -> List[Dict[str, Any]]:
        """Check for conditions that should trigger notifications."""
        try:
            notifications = []
            
            # Check for SOS alerts that need immediate notification
            sos_alerts = db.query(Alert).filter(
                Alert.alert_type == "SOS",
                Alert.status == "NEW",
                Alert.created_at > datetime.utcnow() - timedelta(minutes=5)
            ).all()
            
            for alert in sos_alerts:
                notifications.append({
                    "type": "SOS_EMERGENCY",
                    "priority": "CRITICAL",
                    "tourist_id": alert.tourist_id,
                    "alert_id": alert.id,
                    "message": "EMERGENCY: SOS signal activated",
                    "timestamp": alert.created_at.isoformat(),
                    "requires_response": True
                })
            
            # Check for geofence violations
            geofence_alerts = db.query(Alert).filter(
                Alert.alert_type == "GEOFENCE",
                Alert.priority.in_(["HIGH", "CRITICAL"]),
                Alert.status == "NEW",
                Alert.created_at > datetime.utcnow() - timedelta(minutes=10)
            ).all()
            
            for alert in geofence_alerts:
                notifications.append({
                    "type": "GEOFENCE_VIOLATION",
                    "priority": alert.priority,
                    "tourist_id": alert.tourist_id,
                    "alert_id": alert.id,
                    "message": f"Geofence violation: {alert.title}",
                    "timestamp": alert.created_at.isoformat(),
                    "requires_response": False
                })
            
            # Check for health vitals issues
            health_alerts = db.query(Alert).filter(
                Alert.alert_type == "VITALS",
                Alert.status == "NEW",
                Alert.created_at > datetime.utcnow() - timedelta(minutes=15)
            ).all()
            
            for alert in health_alerts:
                notifications.append({
                    "type": "HEALTH_ALERT",
                    "priority": alert.priority,
                    "tourist_id": alert.tourist_id,
                    "alert_id": alert.id,
                    "message": f"Health alert: {alert.title}",
                    "timestamp": alert.created_at.isoformat(),
                    "requires_response": alert.priority in ["HIGH", "CRITICAL"]
                })
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error checking notification triggers: {str(e)}")
            return []
    
    async def process_message_queue(self):
        """Process queued messages and advisories."""
        try:
            if not self.message_queue:
                return
            
            # Process messages in batches
            batch_size = 10
            messages_to_process = self.message_queue[:batch_size]
            self.message_queue = self.message_queue[batch_size:]
            
            for message in messages_to_process:
                await self.deliver_message(message)
                track_stream_event("notification_sent")
            
            logger.info(f"📨 Processed {len(messages_to_process)} notifications")
            
        except Exception as e:
            logger.error(f"Error processing message queue: {str(e)}")
    
    async def deliver_message(self, message: Dict[str, Any]):
        """Deliver message to tourist (simulated)."""
        try:
            # In a real implementation, this would send push notifications,
            # SMS, or other communication channels
            tourist_id = message.get("tourist_id")
            msg_type = message.get("type", "ADVISORY")
            content = message.get("message", "")
            
            logger.info(f"📱 Delivering {msg_type} to tourist {tourist_id}: {content}")
            
            # Store in local cache for API retrieval
            if tourist_id not in self.advisory_cache:
                self.advisory_cache[tourist_id] = []
            
            self.advisory_cache[tourist_id].append({
                "message": content,
                "type": msg_type,
                "priority": message.get("priority", "LOW"),
                "timestamp": message.get("timestamp", datetime.utcnow().isoformat())
            })
            
            # Keep only last 10 messages per tourist
            self.advisory_cache[tourist_id] = self.advisory_cache[tourist_id][-10:]
            
        except Exception as e:
            logger.error(f"Error delivering message: {str(e)}")
    
    def get_tourist_messages(self, tourist_id: str) -> List[Dict[str, Any]]:
        """Get cached messages for a tourist."""
        return self.advisory_cache.get(tourist_id, [])
    
    async def cleanup_old_data(self):
        """Clean up old notifications and cache data."""
        try:
            # Clean advisory cache (keep only recent)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            for tourist_id in list(self.advisory_cache.keys()):
                messages = self.advisory_cache[tourist_id]
                recent_messages = [
                    msg for msg in messages
                    if datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00")) > cutoff_time
                ]
                
                if recent_messages:
                    self.advisory_cache[tourist_id] = recent_messages
                else:
                    del self.advisory_cache[tourist_id]
            
            logger.info("🧹 Cleaned up old notification data")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")


# Global notification service instance
notification_service = NotificationService()


async def notification_worker():
    """Background worker for processing notifications."""
    logger.info("📨 Starting notification worker...")
    
    while True:
        try:
            db = SessionLocal()
            
            # Generate safety advisories
            advisories = await notification_service.generate_safety_advisories(db)
            for advisory in advisories:
                notification_service.message_queue.append(advisory)
            
            # Check for notification triggers
            notifications = await notification_service.check_notification_triggers(db)
            for notification in notifications:
                notification_service.message_queue.append(notification)
            
            db.close()
            
            # Process message queue
            await notification_service.process_message_queue()
            
            # Clean up old data periodically
            if datetime.utcnow().minute % 30 == 0:  # Every 30 minutes
                await notification_service.cleanup_old_data()
            
            # Sleep for 60 seconds before next cycle
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"❌ Error in notification worker: {str(e)}")
            await asyncio.sleep(120)  # Wait longer on error


async def main():
    """Main service entry point."""
    logger.info("🚀 Starting Notification Service")
    
    # Start background worker
    await notification_worker()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    asyncio.run(main())
