#!/bin/bash
set -e

echo "🚀 Starting MoD Core Safety Backend..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root or with sudo"
    exit 1
fi

# Create necessary directories
mkdir -p /workspace/{logs,data/prometheus,data/grafana}
chown -R prometheus:prometheus /workspace/data/prometheus
chown -R grafana:grafana /workspace/data/grafana

# Generate certificates if they don't exist
if [ ! -f /workspace/ssl-certs/server.crt ]; then
    echo "🔐 Generating SSL certificates..."
    cd /workspace && ./generate_certificates.sh
fi

# Install services if not already done
if [ ! -f /opt/keycloak/bin/kc.sh ]; then
    echo "📦 Installing services..."
    cd /workspace && ./setup_services.sh
fi

# Initialize database if needed
echo "🗄️  Checking database initialization..."
cd /workspace && source venv/bin/activate && python -c "
from app.core.database import SessionLocal
from app.models.tourist import Tourist
db = SessionLocal()
count = db.query(Tourist).count()
if count == 0:
    print('Initializing database...')
    exec(open('init_database.py').read())
else:
    print(f'Database already initialized with {count} tourists')
db.close()
"

# Start all services with supervisor
echo "🎯 Starting all MoD Core services..."
supervisord -c /workspace/configs/supervisor-mod-core.conf

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 15

# Start monitoring services
echo "📊 Starting monitoring services..."
supervisorctl -c /workspace/configs/supervisor-mod-core.conf start monitoring:

# Start security services
echo "🔐 Starting security services..."
supervisorctl -c /workspace/configs/supervisor-mod-core.conf start security:

# Start additional services
echo "🔧 Starting additional services..."
supervisorctl -c /workspace/configs/supervisor-mod-core.conf start services:

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

# Check service status
echo "📊 Service Status:"
supervisorctl -c /workspace/configs/supervisor-mod-core.conf status

# Test core functionality
echo "🧪 Testing core functionality..."
sleep 5

# Test database connection
if su postgres -c "psql -d modcore -p 2026 -c 'SELECT 1;'" >/dev/null 2>&1; then
    echo "✅ Database: Connected"
else
    echo "❌ Database: Connection failed"
fi

# Test API
if curl -s http://localhost:2030/health >/dev/null 2>&1; then
    echo "✅ API: Responding on port 2030"
else
    echo "❌ API: Not responding on port 2030"
fi

# Test Prometheus
if curl -s http://localhost:2028/api/v1/query?query=up >/dev/null 2>&1; then
    echo "✅ Prometheus: Responding on port 2028"
else
    echo "❌ Prometheus: Not responding on port 2028"
fi

# Test Grafana
if curl -s http://localhost:2029/api/health >/dev/null 2>&1; then
    echo "✅ Grafana: Responding on port 2029"
else
    echo "❌ Grafana: Not responding on port 2029"
fi

# Test Keycloak
if curl -s -k https://localhost:2027/realms/master >/dev/null 2>&1; then
    echo "✅ Keycloak: Responding on port 2027"
else
    echo "❌ Keycloak: Not responding on port 2027"
fi

echo ""
echo "🎉 MoD Core startup complete!"
echo ""
echo "📋 Service Access (All ports 2025-2050):"
echo "   🔒 mTLS Proxy: https://localhost:2025 (reverse proxy)"
echo "   🗄️  Database: postgresql://moduser:modpass@localhost:2026/modcore"
echo "   🔐 Keycloak: https://localhost:2027 (OIDC provider)"
echo "   📊 Prometheus: http://localhost:2028 (metrics)"
echo "   📈 Grafana: http://localhost:2029 (dashboards)"
echo "   🌐 API: http://localhost:2030 (FastAPI backend)"
echo "   🔧 Supervisor: http://localhost:2031 (service management)"
echo "   📊 Nginx Stats: http://localhost:2032 (nginx metrics)"
echo ""
echo "🔧 Management Commands:"
echo "   supervisorctl -c /workspace/configs/supervisor-mod-core.conf status"
echo "   supervisorctl -c /workspace/configs/supervisor-mod-core.conf start <service>"
echo "   supervisorctl -c /workspace/configs/supervisor-mod-core.conf restart <service>"
echo ""
