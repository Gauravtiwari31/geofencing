#!/usr/bin/env python3
"""
Basic test of MoD Core API
"""
import sys
sys.path.append('/workspace')

import asyncio
import requests
import json
from datetime import datetime

def test_health_endpoints():
    """Test health endpoints."""
    print("🔍 Testing health endpoints...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {str(e)}")
    
    try:
        # Test ready endpoint
        response = requests.get("http://localhost:8000/ready", timeout=5)
        if response.status_code == 200:
            print("✅ Ready endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Ready endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Ready endpoint error: {str(e)}")


def test_database_connection():
    """Test database connection."""
    print("🗄️  Testing database connection...")
    
    try:
        from app.core.database import SessionLocal
        from app.models.tourist import Tourist
        
        db = SessionLocal()
        tourist_count = db.query(Tourist).count()
        print(f"✅ Database connected, {tourist_count} tourists found")
        db.close()
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")


def main():
    print("🧪 Running MoD Core Basic Tests")
    print("=" * 50)
    
    test_database_connection()
    test_health_endpoints()
    
    print("\n🎯 Basic testing complete!")
    print("\nTo start the FastAPI server, run:")
    print("source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
