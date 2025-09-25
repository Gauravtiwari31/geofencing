#!/bin/bash

echo "🚔 Police SEDI - System Status Check"
echo "===================================="
echo ""

# Check PostgreSQL
if pgrep -x "postgres" > /dev/null; then
    echo "✅ PostgreSQL: Running"
else
    echo "❌ PostgreSQL: Not running"
fi

# Check FastAPI
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo "✅ FastAPI: Running"
else
    echo "❌ FastAPI: Not running"
fi

# Check port availability
if curl -s http://localhost:2035/health > /dev/null 2>&1; then
    echo "✅ Application: Responding on port 2035"
else
    echo "❌ Application: Not responding on port 2035"
fi

# Check database connection
if curl -s http://localhost:2035/health/db 2>/dev/null | grep -q '"status":"healthy"'; then
    echo "✅ Database: Connected"
else
    echo "❌ Database: Connection issues"
fi

echo ""
echo "📊 Quick Stats:"
curl -s http://localhost:2035/api/v1/incidents/stats/dashboard 2>/dev/null | grep -o '"total_incidents":[0-9]*' | head -1 || echo "   Failed to get incident stats"

echo ""
echo "🌐 Access URLs:"
echo "   Main App: http://localhost:2035/"
echo "   API Docs: http://localhost:2035/docs"
echo "   SSE Test: http://localhost:2035/test_sse.html"
