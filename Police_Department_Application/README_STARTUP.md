# Police SEDI Application - Startup Guide

## 🚔 Quick Start

### Option 1: Automated Startup (Recommended)
```bash
cd /workspace
./scripts/start_sedi.sh
```

### Option 2: Manual Step-by-Step

1. **Start PostgreSQL**
   ```bash
   service postgresql start
   ```

2. **Install Python Dependencies**
   ```bash
   cd /workspace
   pip install -r requirements.txt
   ```

3. **Start the Application**
   ```bash
   cd /workspace/backend
   uvicorn main:app --host 0.0.0.0 --port 2035 --reload
   ```

## 🌐 Access Points

Once started, the application will be available at:

- **Main Dashboard**: http://localhost:2035/
- **API Documentation**: http://localhost:2035/docs
- **Health Check**: http://localhost:2035/health
- **SSE Test Page**: http://localhost:2035/test_sse.html

## 🔧 Configuration

The application uses these key configuration files:

- **Environment**: `/workspace/.env`
- **Database**: PostgreSQL on port 2036
- **API Server**: FastAPI on port 2035
- **Frontend**: Served by FastAPI

## 📊 System Requirements

- **Database**: PostgreSQL 14+
- **Python**: 3.8+
- **Memory**: 512MB minimum
- **Ports**: 2035 (API), 2036 (Database)

## 🧪 Testing the Installation

### 1. Health Check
```bash
curl http://localhost:2035/health
```

### 2. Database Test
```bash
curl http://localhost:2035/health/db
```

### 3. API Test
```bash
curl http://localhost:2035/api/v1/incidents/
```

### 4. SSE Test
```bash
# Run the demo script
./scripts/demo_sse.sh

# Or open the visual test
# http://localhost:2035/test_sse.html
```

## 🚨 Troubleshooting

### PostgreSQL Issues
```bash
# Check if PostgreSQL is running
ps aux | grep postgres

# Restart PostgreSQL
service postgresql restart

# Test database connection
PGPASSWORD=sedi_password psql -h localhost -p 2036 -U sedi_user -d sedi_db -c "SELECT 1;"
```

### Python Dependencies
```bash
# If dependencies fail to install
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Port Issues
```bash
# Check what's using the ports
lsof -i :2035
lsof -i :2036

# Kill processes if needed
pkill -f uvicorn
```

### Log Monitoring
```bash
# Monitor application logs
tail -f /var/log/postgresql/postgresql-14-main.log

# Check system processes
ps aux | grep -E "(postgres|uvicorn)"
```

## 🔄 Development Mode

For development with auto-reload:
```bash
cd /workspace/backend
uvicorn main:app --host 0.0.0.0 --port 2035 --reload --log-level debug
```

## 🏭 Production Considerations

For production deployment:

1. **Disable Debug Mode**: Set `DEBUG=false` in `.env`
2. **Use Production WSGI**: Consider Gunicorn instead of Uvicorn
3. **Database**: Use external PostgreSQL instance
4. **Certificates**: Configure SSL/TLS certificates
5. **Monitoring**: Set up proper logging and monitoring

## 📋 Environment Variables

Key environment variables in `/workspace/.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://sedi_user:sedi_password@localhost:2036/sedi_db
POSTGRES_USER=sedi_user
POSTGRES_PASSWORD=sedi_password
POSTGRES_DB=sedi_db

# Application
PORT=2035
DEBUG=true
SECRET_KEY=your-secret-key-here

# MoD Core (for future integration)
MOD_CORE_URL=https://mod-core.example.com
MOD_CORE_STREAM_URL=https://mod-core.example.com/stream

# OIDC (for future integration)
OIDC_ISSUER_URL=https://keycloak.example.com/realms/police
OIDC_CLIENT_ID=sedi-client
OIDC_CLIENT_SECRET=your-client-secret
```

## 🎯 Component Status

| Component | Status | Port | Description |
|-----------|--------|------|-------------|
| PostgreSQL | ✅ Running | 2036 | Database server |
| FastAPI | ✅ Running | 2035 | API server + frontend |
| SSE Stream | ✅ Active | 2035/stream | Real-time events |
| Frontend | ✅ Active | 2035/ | Web dashboard |
| Health Checks | ✅ Active | 2035/health | System monitoring |

## 🔗 API Endpoints

### Core Endpoints
- `GET /` - Frontend dashboard
- `GET /health` - System health
- `GET /docs` - API documentation

### Incidents API
- `GET /api/v1/incidents/` - List incidents
- `GET /api/v1/incidents/{id}` - Get incident details
- `POST /api/v1/incidents/{id}/ack` - Acknowledge incident
- `GET /api/v1/incidents/urgent` - Get urgent incidents
- `GET /api/v1/incidents/stats/dashboard` - Dashboard statistics

### Real-time API
- `GET /api/v1/stream` - SSE event stream
- `GET /api/v1/connections` - Connection statistics
- `POST /api/v1/broadcast/test` - Test broadcast

### Authentication API
- `GET /auth/status` - Auth status (mock)
- `POST /auth/login` - Login (mock)
- `POST /auth/logout` - Logout (mock)

## 🏃‍♂️ Quick Commands

```bash
# Start everything
./scripts/start_sedi.sh

# Demo SSE functionality
./scripts/demo_sse.sh

# Check system status
curl -s http://localhost:2035/health | python3 -m json.tool

# View incidents
curl -s http://localhost:2035/api/v1/incidents/ | python3 -m json.tool

# Test SSE stream (listen for 5 seconds)
timeout 5s curl -N -H "Accept: text/event-stream" http://localhost:2035/api/v1/stream
```
