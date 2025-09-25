# 🚀 MoD Core - Complete Startup Guide

## 📋 **Overview**
This guide provides step-by-step instructions to start the complete MoD Core (Ministry of Tourism Core) system with all services running within the **port range 2025-2050**.

---

## 🎯 **System Architecture**

| Service | Port | Purpose | Status Endpoint |
|---------|------|---------|----------------|
| **PostgreSQL** | 2026 | Database | `psql -h localhost -p 2026 -U moduser modcore` |
| **Keycloak** | 2027 | OIDC Authentication | `https://localhost:2027/realms/master` |
| **Prometheus** | 2028 | Metrics Collection | `http://localhost:2028` |
| **Grafana** | 2029 | Monitoring Dashboards | `http://localhost:2029` |
| **FastAPI** | 2030 | Core API Backend | `http://localhost:2030/health` |
| **Supervisor** | 2031 | Service Management | `http://localhost:2031` |
| **Nginx Stats** | 2032 | Reverse Proxy Metrics | `http://localhost:2032` |

---

## 🏁 **Quick Start (Recommended)**

### **Single Command Startup:**
```bash
cd /workspace
sudo ./start_mod_core.sh
```

This script will:
- ✅ Generate SSL certificates if needed
- ✅ Install missing services automatically  
- ✅ Initialize the database with sample data
- ✅ Start all services via supervisor
- ✅ Perform health checks
- ✅ Display service access URLs

---

## 🔧 **Manual Step-by-Step Startup**

### **1. Prerequisites Check**
```bash
cd /workspace

# Check if running as root (required for supervisor)
sudo whoami

# Verify Python virtual environment
source venv/bin/activate
python --version

# Check dependencies
pip list | grep -E "(fastapi|uvicorn|sqlalchemy|prometheus)"
```

### **2. SSL Certificates**
```bash
# Generate certificates if they don't exist
if [ ! -f ssl-certs/server.crt ]; then
    ./generate_certificates.sh
fi

# Verify certificates
ls -la ssl-certs/
```

### **3. Install Services** (if first time)
```bash
# Install Keycloak, Prometheus, Grafana
./setup_services.sh
```

### **4. Database Initialization**
```bash
# Start PostgreSQL first
sudo supervisord -c configs/supervisor-mod-core.conf
sudo supervisorctl -c configs/supervisor-mod-core.conf start core:mod-db

# Wait for DB to start
sleep 5

# Initialize database with sample data
source venv/bin/activate
python init_database.py
```

### **5. Start All Services**
```bash
# Start supervisor daemon
sudo supervisord -c configs/supervisor-mod-core.conf

# Start core services
sudo supervisorctl -c configs/supervisor-mod-core.conf start core:

# Start monitoring services  
sudo supervisorctl -c configs/supervisor-mod-core.conf start monitoring:

# Start security services
sudo supervisorctl -c configs/supervisor-mod-core.conf start security:

# Start additional services
sudo supervisorctl -c configs/supervisor-mod-core.conf start services:
```

### **6. Verify Services**
```bash
# Check all service status
sudo supervisorctl -c configs/supervisor-mod-core.conf status

# Expected output:
# core:mod-api                     RUNNING   pid 12345, uptime 0:01:23
# core:mod-db                      RUNNING   pid 12346, uptime 0:01:23  
# monitoring:grafana               RUNNING   pid 12347, uptime 0:01:23
# monitoring:prometheus            RUNNING   pid 12348, uptime 0:01:23
# security:keycloak                RUNNING   pid 12349, uptime 0:01:23
# services:eth-adapter             RUNNING   pid 12350, uptime 0:01:23
# services:notifier                RUNNING   pid 12351, uptime 0:01:23
```

---

## 🧪 **Health Checks & Testing**

### **Service Health Verification:**
```bash
# 1. Database Connection
psql -h localhost -p 2026 -U moduser -d modcore -c "SELECT 1;"

# 2. FastAPI Backend
curl http://localhost:2030/health
# Expected: {"status":"healthy","version":"1.0.0","timestamp":...}

# 3. Prometheus Metrics
curl http://localhost:2028/api/v1/query?query=up
# Expected: JSON with metrics data

# 4. Grafana Dashboard
curl http://localhost:2029/api/health
# Expected: {"commit":"...","database":"ok","version":"10.1.2"}

# 5. Keycloak OIDC
curl -k https://localhost:2027/realms/master
# Expected: JSON realm configuration
```

### **Authentication Testing:**
```bash
# Get Tourist Authentication Token
curl -k -X POST "https://host.docker.internal:2027/realms/mod-core/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=tourist-app" \
  -d "username=tourist-demo" \
  -d "password=tourist123"

# Get Police Authentication Token  
curl -k -X POST "https://host.docker.internal:2027/realms/mod-core/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=police-sedi" \
  -d "client_secret=police-sedi-secret-2025"
```

### **API Endpoint Testing:**
```bash
# Health Check
curl http://localhost:2030/health

# Readiness Check
curl http://localhost:2030/ready

# API Documentation
curl http://localhost:2030/docs

# Metrics Endpoint
curl http://localhost:2030/metrics

# Test Authenticated Endpoints (use tokens from above)
TOURIST_TOKEN="your_tourist_access_token"
POLICE_TOKEN="your_police_access_token"

# Tourist endpoint
curl -H "Authorization: Bearer $TOURIST_TOKEN" \
     "http://localhost:2030/v1/app/fences/summary?lat=26.162&lon=91.779"

# Police stream endpoint
curl -H "Authorization: Bearer $POLICE_TOKEN" \
     "http://localhost:2030/v1/police/stream"
```

---

## 🌐 **Access URLs**

### **Web Interfaces:**
- **📊 Grafana Dashboards:** `http://localhost:2029`
  - Username: `admin` 
  - Password: `admin123`
  
- **📈 Prometheus:** `http://localhost:2028`
  - Query interface for metrics
  
- **🔐 Keycloak Admin:** `https://localhost:2027` 
  - Admin Console for user management
  
- **🔧 Supervisor:** `http://localhost:2031`
  - Service management interface

### **API Endpoints:**
- **🚀 Core API:** `http://localhost:2030`
  - Health: `/health`
  - Ready: `/ready` 
  - Docs: `/docs`
  - Metrics: `/metrics`

---

## 🛠️ **Service Management Commands**

### **Supervisor Management:**
```bash
# Check status of all services
sudo supervisorctl -c configs/supervisor-mod-core.conf status

# Start a specific service
sudo supervisorctl -c configs/supervisor-mod-core.conf start <service_name>

# Stop a specific service  
sudo supervisorctl -c configs/supervisor-mod-core.conf stop <service_name>

# Restart a service
sudo supervisorctl -c configs/supervisor-mod-core.conf restart <service_name>

# Start all services in a group
sudo supervisorctl -c configs/supervisor-mod-core.conf start monitoring:
sudo supervisorctl -c configs/supervisor-mod-core.conf start security:
sudo supervisorctl -c configs/supervisor-mod-core.conf start core:
```

### **Individual Service Control:**
```bash
# View service logs
sudo supervisorctl -c configs/supervisor-mod-core.conf tail <service_name>
sudo supervisorctl -c configs/supervisor-mod-core.conf tail -f <service_name>

# Available service names:
# - core:mod-api (FastAPI backend)
# - core:mod-db (PostgreSQL database)  
# - monitoring:grafana (Dashboard)
# - monitoring:prometheus (Metrics)
# - security:keycloak (OIDC provider)
# - security:mod-proxy (Nginx reverse proxy)
# - services:eth-adapter (Ethereum integration)
# - services:notifier (Notification service)
```

---

## 🛑 **Shutdown Commands**

### **Graceful Shutdown:**
```bash
# Stop all services
sudo supervisorctl -c configs/supervisor-mod-core.conf stop all

# Stop supervisor daemon
sudo supervisorctl -c configs/supervisor-mod-core.conf shutdown

# Alternative: Kill supervisor process
sudo pkill supervisord
```

### **Emergency Stop:**
```bash
# Force kill all services
sudo pkill -f "grafana"
sudo pkill -f "uvicorn" 
sudo pkill -f "prometheus"
sudo pkill -f "keycloak"
sudo pkill -f "supervisord"
```

---

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **1. "Permission denied" errors:**
```bash
# Run commands with sudo
sudo ./start_mod_core.sh
```

#### **2. "Port already in use" errors:**
```bash
# Check what's using the port
sudo netstat -tlnp | grep :2030

# Kill conflicting processes
sudo pkill -f "port:2030"
```

#### **3. Database connection errors:**
```bash
# Check if PostgreSQL is running
sudo supervisorctl -c configs/supervisor-mod-core.conf status core:mod-db

# Restart database
sudo supervisorctl -c configs/supervisor-mod-core.conf restart core:mod-db

# Check logs
sudo supervisorctl -c configs/supervisor-mod-core.conf tail core:mod-db
```

#### **4. SSL certificate errors:**
```bash
# Regenerate certificates
rm -rf ssl-certs/
./generate_certificates.sh
```

#### **5. Service won't start:**
```bash
# Check logs for specific service
sudo supervisorctl -c configs/supervisor-mod-core.conf tail <service_name>

# Check supervisor logs
tail -f logs/supervisord.log

# Restart supervisor
sudo supervisorctl -c configs/supervisor-mod-core.conf reload
```

### **Log Locations:**
- **Supervisor:** `/workspace/logs/supervisord.log`
- **FastAPI:** `/workspace/logs/mod-api.log`
- **Database:** `/workspace/logs/postgresql.log`  
- **Grafana:** `/workspace/logs/grafana.log`
- **Prometheus:** `/workspace/logs/prometheus.log`
- **Keycloak:** `/workspace/logs/keycloak.log`

---

## 📝 **Port Reference**

| Port | Service | Protocol | Purpose |
|------|---------|----------|---------|
| 2025 | nginx proxy | HTTPS | mTLS reverse proxy (when enabled) |
| 2026 | PostgreSQL | TCP | Database connections |
| 2027 | Keycloak | HTTPS | OIDC authentication |
| 2028 | Prometheus | HTTP | Metrics collection |
| 2029 | Grafana | HTTP | Monitoring dashboards |
| 2030 | FastAPI | HTTP | Core API backend |
| 2031 | Supervisor | HTTP | Service management |
| 2032 | nginx stats | HTTP | Reverse proxy metrics |

**⚠️ Important:** All services are configured to run ONLY within ports 2025-2050 range as required.

---

## ✅ **Success Verification**

When startup is complete, you should see:

```bash
🎉 DEPLOYMENT COMPLETE!

✅ All services running in port range 2025-2050:
   📊 Database (PostgreSQL): localhost:2026
   🔐 Keycloak (OIDC): localhost:2027  
   📈 Prometheus: localhost:2028
   📋 Grafana: localhost:2029
   🚀 FastAPI: localhost:2030
   🔧 Supervisor: localhost:2031

🧪 Service Health Check:
{"status":"healthy","version":"1.0.0","timestamp":...}
```

**🎯 Your MoD Core system is now fully operational!**
