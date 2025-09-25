"""
Simple test script to verify database models are working
"""

import asyncio
from datetime import datetime
from models.database import get_db_session
from models.models import Incident
from models.schemas import IncidentCreate, LocationData
from services.incident_service import IncidentService


async def test_incident_operations():
    """Test basic incident CRUD operations"""
    print("🧪 Testing database models...")
    
    async with get_db_session() as db:
        # Test creating an incident
        location_data = LocationData(lat=40.7128, lng=-74.0060, accuracy=10)
        incident_data = IncidentCreate(
            alert_id=999999,
            tourist_id="test-tourist-123",
            type="SOS",
            created_at=datetime.utcnow(),
            location=location_data,
            score_band="HIGH",
            details="Test incident for model verification"
        )
        
        # Create incident
        incident = await IncidentService.create_incident(db, incident_data)
        print(f"✅ Created incident: {incident.alert_id}")
        
        # Retrieve incident
        retrieved = await IncidentService.get_incident(db, incident.alert_id)
        print(f"✅ Retrieved incident: {retrieved.alert_id} - {retrieved.type}")
        
        # Check location data
        if retrieved.location:
            print(f"✅ Location data: lat={retrieved.location['lat']}, lng={retrieved.location['lng']}")
        
        # Get statistics
        stats = await IncidentService.get_incident_statistics(db)
        print(f"✅ Statistics: {stats.total_incidents} total, {stats.active_incidents} active")
        
        print("🎉 All database tests passed!")


if __name__ == "__main__":
    asyncio.run(test_incident_operations())
