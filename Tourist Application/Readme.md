
# Smart Tourist Safety System 🛡️🌍

## Overview

The **Smart Tourist Safety System** is a tech-driven platform designed to enhance tourist security through **blockchain-based digital IDs, geo-fencing, AI-powered anomaly detection, and IoT wearables**.

The solution ensures real-time safety monitoring while respecting privacy and offering a user-friendly experience — particularly useful in remote or high-risk regions.

---

## Key Features 🚀

### 🔐 Blockchain Digital ID

* Tourists register at entry points and receive a **tamper-proof digital ID** on a blockchain.
* IDs are verifiable via QR codes/digital certificates.
* Data privacy ensured using decentralized identity management.

### 📱 Tourist Mobile Application

* **Safety Score**: Calculates a real-time score based on location, time, and risk factors.
* **Geo-fencing Alerts**: Warns tourists and notifies authorities if entering unsafe zones.
* **SOS Panic Button**: Sends live GPS location & ID to police and emergency contacts.
* **Real-Time Tracking (Opt-in)**: Families or authorities can follow tourist location (with consent).
* **Multilingual & Accessible**: Support for multiple Indian languages, voice commands, and accessibility features.

### 🤖 AI Anomaly Detection

* Detects unusual patterns like:

  * Prolonged inactivity.
  * Sudden falls or sharp altitude changes.
  * Deviations from planned itinerary.
* Auto-generates alerts and missing person reports (E-FIR simulation).

### 🖥️ Tourism & Police Dashboard

* Real-time map with tourist locations & safety status.
* Incident/alert management (SOS, geofence, AI triggers).
* Tourist profile verification via blockchain.
* High-risk zone updates, broadcast messaging, and analytics.

### ⌚ IoT Wearables (ESP32 Prototype)

* Smart band with **SOS button, motion & health sensors**.
* Streams real-time vitals and auto-triggers alerts for anomalies.
* Works alongside the mobile app for enhanced safety.

---

## Tech Stack 🛠️

* **Blockchain**: Hyperledger Fabric / Ethereum (for MVP).
* **Backend**: Node.js + Express / Python (FastAPI/Flask) for APIs & AI services.
* **Database**: PostgreSQL + PostGIS (geo-queries), MongoDB (logs).
* **Mobile App**: Flutter (cross-platform) or Native Android (Kotlin).
* **Dashboard**: React + Leaflet/Google Maps API.
* **IoT Devices**: ESP32 (C++/Arduino IDE or MicroPython).

---

## MVP Roadmap 🗺️

**Phase 1: Core Functionality**

* Tourist registration & digital ID issuance.
* Basic mobile app with SOS + location tracking.
* Simple dashboard for monitoring alerts.

**Phase 2: Enhancements**

* Full geo-fencing + safety score system.
* AI anomaly detection (rule-based).
* IoT SOS wearable integration.
* Dashboard with real-time map & heatmaps.

**Phase 3: Pilot Deployment**

* Full blockchain integration.
* Advanced AI models for predictive safety.
* Family/friends live tracking portal.
* Production-grade IoT hardware & emergency service integration.

---

## Getting Started ⚡

### Prerequisites

* Node.js (>=16) / Python (>=3.9)
* PostgreSQL / MongoDB
* Flutter SDK (for mobile app)
* Arduino IDE (for IoT devices)

### Installation

```bash
# Clone repo
git clone https://github.com/your-username/smart-tourist-safety.git

# Navigate to project
cd smart-tourist-safety

# Install dependencies
npm install   # or pip install -r requirements.txt
```

---

## Contributors 🤝

This project is developed as an **innovation-driven safety solution** for tourists, combining modern technologies with real-world applicability.

---
