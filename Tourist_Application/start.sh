#!/bin/bash

# Tourist Mobile Simulator Startup Script

echo "🗺️ Starting Tourist Mobile Simulator"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: Please run this script from the /workspace directory"
    exit 1
fi

# Set Python path
export PYTHONPATH=/workspace

# Default environment variables for development
export GATEWAY_URL=${GATEWAY_URL:-"http://localhost:2045"}
export GATEWAY_MQTT_HOST=${GATEWAY_MQTT_HOST:-"localhost"}
export GATEWAY_MQTT_PORT=${GATEWAY_MQTT_PORT:-"2046"}
export KEYCLOAK_URL=${KEYCLOAK_URL:-"https://localhost:2027"}
export KEYCLOAK_REALM=${KEYCLOAK_REALM:-"mod-core"}
export KEYCLOAK_CLIENT_ID=${KEYCLOAK_CLIENT_ID:-"tourist-app"}
export DEVICE_ID=${DEVICE_ID:-"tourist-sim-001"}

# Display configuration
echo "Configuration:"
echo "  App Port: 2040"
echo "  Gateway URL: $GATEWAY_URL"
echo "  Gateway MQTT: $GATEWAY_MQTT_HOST:$GATEWAY_MQTT_PORT"
echo "  Keycloak URL: $KEYCLOAK_URL"
echo "  Device ID: $DEVICE_ID"
echo ""

# Start the application
echo "🚀 Starting FastAPI server on http://0.0.0.0:2040"
echo "   Open your browser to: http://localhost:2040"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

uvicorn backend.main:app --host 0.0.0.0 --port 2040 --reload
