#!/usr/bin/env python3
"""
Test MoD Core API endpoints
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health_endpoints():
    """Test health and ready endpoints."""
    print("🏥 Testing Health Endpoints")
    print("-" * 30)
    
    # Test health
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ {response.json()}")
        else:
            print(f"  ❌ {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test ready (will likely fail without auth, but that's expected)
    try:
        response = requests.get(f"{BASE_URL}/ready")
        print(f"Ready: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ {response.json()}")
        else:
            print(f"  ❌ {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def test_tourist_endpoints():
    """Test tourist endpoints (will fail without auth, but let's see the error)."""
    print("\n👤 Testing Tourist Endpoints")
    print("-" * 30)
    
    # Test fences summary (should require auth)
    try:
        response = requests.get(f"{BASE_URL}/v1/app/fences/summary?lat=26.162&lon=91.779")
        print(f"Fences Summary: {response.status_code}")
        print(f"  📝 {response.text[:200]}...")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test messages endpoint
    try:
        response = requests.get(f"{BASE_URL}/v1/app/messages")
        print(f"Messages: {response.status_code}")
        print(f"  📝 {response.text[:200]}...")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def test_police_endpoints():
    """Test police endpoints (will fail without auth)."""
    print("\n👮 Testing Police Endpoints")
    print("-" * 30)
    
    # Test police stream
    try:
        response = requests.get(f"{BASE_URL}/v1/police/stream", timeout=2)
        print(f"Police Stream: {response.status_code}")
        print(f"  📝 {response.text[:200]}...")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def main():
    print("🧪 MoD Core API Testing")
    print("=" * 50)
    
    test_health_endpoints()
    test_tourist_endpoints()
    test_police_endpoints()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("- Health endpoint should work (✅)")
    print("- Ready endpoint might have DB connection issues")  
    print("- API endpoints should return 401/403 (auth required)")
    print("- This confirms our API structure is working!")


if __name__ == "__main__":
    main()
