#!/bin/bash

# MoT Core Dashboard Startup Script
echo "🚀 Starting Ministry of Tourism Core Dashboard..."

# Kill any existing servers
pkill -f "uvicorn.*8000" 2>/dev/null

# Activate virtual environment
source /workspace/venv/bin/activate

# Start the dashboard server
echo "📡 Starting dashboard server on http://localhost:8000"
cd /workspace
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Wait for server to start
sleep 3

# Check if server is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Dashboard server is running!"
    echo ""
    echo "🌐 Access your MoT Core Dashboard at:"
    echo "   http://localhost:8000"
    echo ""
    echo "📊 API Endpoints:"
    echo "   http://localhost:8000/docs (API Documentation)"
    echo "   http://localhost:8000/api/v1/tourists/live (Live Tourist Data)"
    echo "   http://localhost:8000/api/v1/alerts/active (Active Alerts)"
    echo ""
    echo "🎯 Features Available:"
    echo "   ✓ Real-time tourist tracking with <3s refresh"
    echo "   ✓ Interactive map with multiple view modes"
    echo "   ✓ Red zone drawing and management"
    echo "   ✓ Tourist lists with safety status"
    echo "   ✓ Police action buttons with E-FIR generation"
    echo "   ✓ WebSocket support for real-time updates"
    echo "   ✓ Critical alerts monitoring"
    echo ""
    echo "🔴 To draw red zones: Click 'Draw Red Zone' button on the map"
    echo "🚔 To trigger police action: Click 'Police Action' next to any tourist"
    echo ""
else
    echo "❌ Failed to start dashboard server"
    echo "🔍 Check logs for errors:"
    echo "   tail -f /workspace/logs/*.log"
fi
