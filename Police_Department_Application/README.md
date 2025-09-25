# Police SEDI Application

**Security & Emergency Data Interface** - Real-time incident monitoring system for police operations.

## Overview

The Police SEDI application consumes live incident streams from the Ministry of Defense (MoD) Core system and provides:
- Real-time incident monitoring and display
- Interactive map visualization with OpenStreetMap
- Incident acknowledgment and response tracking
- Secure authentication via OIDC with Keycloak
- mTLS communication with MoD Core

## Architecture

- **Backend**: FastAPI (Python) serving REST API and SSE streams
- **Frontend**: React with TypeScript and Leaflet maps
- **Database**: PostgreSQL 14 (local, port 2036)
- **Deployment**: Single container on Ubuntu 22.04

## Quick Start

### Prerequisites
- Ubuntu 22.04 container with Python 3.10, Node.js 12.22, PostgreSQL 14
- Client certificates for mTLS communication with MoD Core
- OIDC configuration for Keycloak authentication

### Setup & Run

1. **Start the application**:
   ```bash
   ./scripts/start_sedi.sh
   ```

2. **Access the application**:
   - Main UI: https://localhost:2035
   - API Docs: https://localhost:2035/docs
   - Health Check: https://localhost:2035/health

### Manual Setup

1. **Database Setup** (already configured):
   ```bash
   # PostgreSQL is running on port 2036
   # Database: sedi_db, User: sedi_user
   ```

2. **Backend Setup**:
   ```bash
   cd /workspace
   pip install -r requirements.txt
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 2035 --reload
   ```

3. **Frontend Setup** (development):
   ```bash
   cd frontend
   npm install
   npm run dev  # Runs on port 3000 with proxy to backend
   ```

## Project Structure

```
/workspace/
├── backend/                 # FastAPI application
│   ├── main.py             # Application entry point
│   ├── config.py           # Configuration management
│   ├── auth/               # OIDC authentication
│   ├── services/           # Business logic (MoD integration, SSE)
│   ├── models/             # Database models and schemas
│   └── api/                # REST API endpoints
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API clients and SSE
│   │   ├── store/          # State management
│   │   └── types/          # TypeScript definitions
│   ├── vite.config.ts      # Vite configuration
│   └── package.json        # Dependencies
├── database/               # Database schema and migrations
├── scripts/                # Deployment and utility scripts
├── certs/                  # TLS certificates (mounted)
├── config.env              # Environment configuration
└── requirements.txt        # Python dependencies
```

## Configuration

Environment variables are loaded from `config.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://sedi_user:sedi_password@localhost:2036/sedi_db

# MoD Core
MOD_CORE_URL=https://<MoD_IP>:2025
MOD_CLIENT_CERT_PATH=/workspace/certs/sedi.crt
MOD_CLIENT_KEY_PATH=/workspace/certs/sedi.key

# OIDC
OIDC_ISSUER_URL=https://keycloak.example.com/auth/realms/police
OIDC_CLIENT_ID=sedi-police-app
```

## API Endpoints

### Authentication
- `GET /auth/login` - Initiate OIDC login
- `GET /auth/callback` - OIDC callback handler
- `POST /auth/logout` - Logout

### Incidents
- `GET /api/v1/incidents` - List incidents (with filters)
- `GET /api/v1/incidents/{alert_id}` - Get incident details
- `POST /api/v1/incidents/{alert_id}/ack` - Acknowledge incident

### Real-time
- `GET /api/v1/stream` - SSE stream for live updates

## Development

### Backend Development
```bash
cd backend
uvicorn main:app --reload --port 2035
```

### Frontend Development
```bash
cd frontend
npm run dev  # Hot reload on port 3000
```

### Database Access
```bash
PGPASSWORD=sedi_password psql -h localhost -p 2036 -U sedi_user -d sedi_db
```

## Security

- **Authentication**: OIDC with Keycloak (POLICE role required)
- **mTLS**: Client certificate authentication with MoD Core
- **HTTPS**: All communications encrypted
- **Data Retention**: Minimal incident data, no PII storage

## Monitoring

- Health check: `GET /health`
- Database status, MoD Core connectivity
- Real-time incident processing metrics
