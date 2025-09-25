#!/usr/bin/env python3
"""
Initialize MoD Core database schema and sample data
"""
import sys
import os
sys.path.append('/workspace')

from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.database import Base
from app.models.tourist import Tourist, Device, Location, DigitalId, Consent
from app.models.geofence import Geofence, GeofenceEvent
from app.models.alert import Alert, AlertAcknowledgment, IncidentReport, AuditLog

settings = get_settings()

def init_database():
    """Initialize database with schema and sample data."""
    print("🗄️  Initializing MoD Core database...")
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    # Create all tables
    print("📋 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_tourists = db.query(Tourist).count()
        if existing_tourists > 0:
            print("✅ Database already initialized")
            return
        
        print("🌱 Creating sample data...")
        
        # Create sample tourist
        sample_tourist = Tourist(
            id="b1d0b691-2a3e-4f5c-8b9a-1234567890ab",
            digital_id_hash="abc123def456",
            emergency_contact={
                "name": "John Doe Emergency Contact",
                "phone": "+91-9876543210",
                "email": "emergency@example.com"
            }
        )
        db.add(sample_tourist)
        
        # Create sample device
        sample_device = Device(
            tourist_id=sample_tourist.id,
            hw_id="device-001",
            device_type="android",
            last_seen=datetime.utcnow()
        )
        db.add(sample_device)
        
        # Create sample consent
        sample_consent = Consent(
            tourist_id=sample_tourist.id,
            live_share=True,
            emergency_sharing=True,
            police_sharing=True
        )
        db.add(sample_consent)
        
        # Commit tourist and device before creating location
        db.commit()
        db.refresh(sample_device)
        
        # Create sample geofences
        # Red zone (restricted area)
        red_zone = Geofence(
            name="Restricted Military Area",
            description="High security military installation",
            severity=10,
            zone_type="red_zone",
            geom="POLYGON((91.770 26.150, 91.780 26.150, 91.780 26.160, 91.770 26.160, 91.770 26.150))",
            active=True,
            created_by="system"
        )
        db.add(red_zone)
        
        # Caution zone
        caution_zone = Geofence(
            name="Construction Area",
            description="Active construction zone",
            severity=5,
            zone_type="caution",
            geom="POLYGON((91.765 26.155, 91.775 26.155, 91.775 26.165, 91.765 26.165, 91.765 26.155))",
            active=True,
            created_by="system"
        )
        db.add(caution_zone)
        
        # Create sample location (safe area)
        sample_location = Location(
            tourist_id=sample_tourist.id,
            device_id=sample_device.id,
            recorded_at=datetime.utcnow(),
            geom="POINT(91.779 26.162)",  # Near but outside restricted area
            speed_mps=1.2,
            altitude=53.4,
            location_metadata={
                "heart_rate": 75,
                "battery": 0.85,
                "temperature": 25.5
            }
        )
        db.add(sample_location)
        
        # Commit initial data
        db.commit()
        
        print("✅ Sample data created:")
        print(f"   📱 Tourist: {sample_tourist.id}")
        print(f"   📱 Device: {sample_device.hw_id}")
        print(f"   🗺️  Geofences: {red_zone.name}, {caution_zone.name}")
        print(f"   📍 Location: 26.162°N, 91.779°E")
        
        # Test PostGIS functionality
        print("🗺️  Testing PostGIS functionality...")
        
        # Test distance calculation
        result = db.execute(text("""
            SELECT ST_Distance(
                ST_Transform(ST_GeomFromText('POINT(91.779 26.162)', 4326), 3857),
                ST_Transform(geom, 3857)
            ) as distance
            FROM geofences 
            WHERE name = 'Restricted Military Area'
        """)).fetchone()
        
        if result:
            distance = result[0]
            print(f"   ✅ Distance to red zone: {distance:.1f} meters")
        
        # Test geofence containment
        in_geofence = db.execute(text("""
            SELECT name FROM geofences 
            WHERE ST_Contains(geom, ST_GeomFromText('POINT(91.779 26.162)', 4326))
        """)).fetchall()
        
        if in_geofence:
            print(f"   ⚠️  Point is inside: {[row[0] for row in in_geofence]}")
        else:
            print("   ✅ Point is in safe area")
        
        print("🎯 Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
