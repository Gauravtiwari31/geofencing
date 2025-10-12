#!/usr/bin/env python3
import os
import time
import json
import random
import requests
from datetime import datetime, timezone

# Configuration via environment variables
TARGET_URL = os.getenv("TARGET_URL", "http://localhost:2030/v1/app/ingest")
HEARTBEAT_SECONDS = int(os.getenv("HEARTBEAT_SECONDS", "5"))
START_LAT = float(os.getenv("START_LAT", "26.1625"))
START_LNG = float(os.getenv("START_LNG", "91.7794"))
JITTER_METERS = float(os.getenv("JITTER_METERS", "3"))  # random walk jitter
DEVICE_ID = os.getenv("DEVICE_ID", "tourist-sim-001")
APP_BUILD = os.getenv("APP_BUILD_VERSION", "1.0.0")
APP_PLATFORM = os.getenv("APP_PLATFORM", "headless")

# Convert meter jitter to degrees (approx)
# 1 deg lat ~ 111,111 m; 1 deg lng ~ 111,111 m * cos(lat)
LAT_DEG_PER_M = 1.0 / 111111.0


def jitter(lat: float, lng: float):
    lat_j = lat + (random.uniform(-JITTER_METERS, JITTER_METERS) * LAT_DEG_PER_M)
    lng_deg_per_m = LAT_DEG_PER_M * max(0.1, abs(__import__("math").cos(__import__("math").radians(lat))))
    lng_j = lng + (random.uniform(-JITTER_METERS, JITTER_METERS) * lng_deg_per_m)
    return lat_j, lng_j


def build_payload(lat: float, lng: float):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "tourist_id": None,
        "device_id": DEVICE_ID,
        "position": {
            "lat": lat,
            "lng": lng,
            "alt": None,
            "speed_mps": None,
            "ts": now
        },
        "health": {
            "heart_rate": None,
            "fall_detected": None,
            "battery": None
        },
        "sos": None,
        "app": {
            "build": APP_BUILD,
            "platform": APP_PLATFORM
        }
    }


def send_heartbeat(lat: float, lng: float):
    payload = build_payload(lat, lng)
    headers = {"Content-Type": "application/json"}
    try:
        r = requests.post(TARGET_URL, headers=headers, data=json.dumps(payload), timeout=10)
        ok = 200 <= r.status_code < 300
        print(f"[{datetime.now().isoformat()}] POST {TARGET_URL} -> {r.status_code} {'OK' if ok else r.text}")
        return ok
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ERROR sending heartbeat: {e}")
        return False


def main():
    lat, lng = START_LAT, START_LNG
    print("Heartbeat sender starting...")
    print(f"Target: {TARGET_URL}")
    print(f"Interval: {HEARTBEAT_SECONDS}s | Start: {lat:.6f},{lng:.6f} | Device: {DEVICE_ID}")
    while True:
        send_heartbeat(lat, lng)
        lat, lng = jitter(lat, lng)
        time.sleep(HEARTBEAT_SECONDS)


if __name__ == "__main__":
    main()
