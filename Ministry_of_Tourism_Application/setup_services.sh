#!/bin/bash
set -e

echo "🚀 Setting up MoD Core services..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root or with sudo"
    exit 1
fi

# Update system packages
echo "📦 Updating system packages..."
apt-get update -qq

# Install PostgreSQL + PostGIS
echo "🗄️  Installing PostgreSQL and PostGIS..."
apt-get install -y --no-install-recommends \
    postgresql-14 \
    postgresql-14-postgis-3 \
    postgresql-contrib-14 \
    postgresql-client-14

# Install Nginx
echo "🌐 Installing Nginx..."
apt-get install -y nginx

# Install Java for Keycloak
echo "☕ Installing Java 17..."
apt-get install -y openjdk-17-jdk

# Install supervisor for process management
echo "👔 Installing Supervisor..."
apt-get install -y supervisor

# Install additional tools
echo "🔧 Installing additional tools..."
apt-get install -y wget curl unzip jq

# Create service users
echo "👥 Creating service users..."
id -u keycloak &>/dev/null || useradd -r -s /bin/false keycloak
id -u prometheus &>/dev/null || useradd -r -s /bin/false prometheus  
id -u grafana &>/dev/null || useradd -r -s /bin/false grafana

# Create directories
echo "📁 Creating service directories..."
mkdir -p /opt/{keycloak,prometheus,grafana}
mkdir -p /var/log/mod-core
mkdir -p /workspace/{logs,data,configs}

# Download and setup Keycloak
echo "🔐 Setting up Keycloak..."
cd /opt
if [ ! -f keycloak/bin/kc.sh ]; then
    wget -q https://github.com/keycloak/keycloak/releases/download/22.0.3/keycloak-22.0.3.tar.gz
    tar -xzf keycloak-22.0.3.tar.gz
    rm -rf keycloak-22.0.3.tar.gz
    mv keycloak-22.0.3/* keycloak/
    rmdir keycloak-22.0.3
    chown -R keycloak:keycloak keycloak/
fi

# Download and setup Prometheus
echo "📊 Setting up Prometheus..."
if [ ! -f prometheus/prometheus ]; then
    wget -q https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.linux-amd64.tar.gz
    tar -xzf prometheus-2.47.0.linux-amd64.tar.gz
    rm -rf prometheus-2.47.0.linux-amd64.tar.gz
    mv prometheus-2.47.0.linux-amd64/* prometheus/
    rmdir prometheus-2.47.0.linux-amd64
    chown -R prometheus:prometheus prometheus/
    mkdir -p prometheus/data
    chown prometheus:prometheus prometheus/data
fi

# Download and setup Grafana
echo "📈 Setting up Grafana..."
if [ ! -f grafana/bin/grafana-server ]; then
    wget -q https://dl.grafana.com/enterprise/release/grafana-enterprise-10.1.2.linux-amd64.tar.gz
    tar -xzf grafana-enterprise-10.1.2.linux-amd64.tar.gz
    rm -rf grafana-enterprise-10.1.2.linux-amd64.tar.gz
    mv grafana-10.1.2/* grafana/
    rmdir grafana-10.1.2
    chown -R grafana:grafana grafana/
    mkdir -p grafana/data
    chown grafana:grafana grafana/data
fi

# Setup Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd /workspace
if [ ! -d venv ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
else
    echo "Virtual environment already exists"
fi

# Setup PostgreSQL
echo "🔧 Configuring PostgreSQL..."
if [ ! -d /var/lib/postgresql/14/main ]; then
    su postgres -c "/usr/lib/postgresql/14/bin/initdb -D /var/lib/postgresql/14/main"
fi

# Configure PostgreSQL
echo "port = 2026" >> /etc/postgresql/14/main/postgresql.conf
echo "listen_addresses = 'localhost'" >> /etc/postgresql/14/main/postgresql.conf
echo "max_connections = 100" >> /etc/postgresql/14/main/postgresql.conf

# Start PostgreSQL temporarily to create database
echo "🚀 Starting PostgreSQL temporarily..."
su postgres -c "/usr/lib/postgresql/14/bin/pg_ctl start -D /var/lib/postgresql/14/main -l /workspace/logs/postgresql.log"

# Wait for PostgreSQL to start
sleep 5

# Create database and user
echo "🗄️  Creating MoD Core database..."
su postgres -c "createuser --no-password moduser" 2>/dev/null || echo "User moduser already exists"
su postgres -c "createdb modcore" 2>/dev/null || echo "Database modcore already exists"
su postgres -c "psql -c \"ALTER USER moduser WITH PASSWORD 'modpass';\"" 2>/dev/null
su postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE modcore TO moduser;\"" 2>/dev/null

# Enable PostGIS
echo "🗺️  Enabling PostGIS extensions..."
su postgres -c "psql -d modcore -c \"CREATE EXTENSION IF NOT EXISTS postgis;\"" 2>/dev/null
su postgres -c "psql -d modcore -c \"CREATE EXTENSION IF NOT EXISTS postgis_topology;\"" 2>/dev/null

# Stop PostgreSQL (will be managed by supervisor)
echo "⏹️  Stopping PostgreSQL..."
su postgres -c "/usr/lib/postgresql/14/bin/pg_ctl stop -D /var/lib/postgresql/14/main"

# Set permissions
echo "🔒 Setting up permissions..."
chown -R www-data:www-data /workspace
chmod +x /workspace/*.sh

echo "✅ MoD Core services setup complete!"
echo ""
echo "Next steps:"
echo "1. Run: ./generate_certificates.sh"
echo "2. Run: ./start_mod_core.sh"
echo ""
