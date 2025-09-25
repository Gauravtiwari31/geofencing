#!/bin/bash
set -e

echo "🚔 Police SEDI Application - Startup Script"
echo "==========================================="
echo ""

# Function to print step info
print_step() {
    echo "📋 Step $1: $2"
    echo "   → $3"
    echo ""
}

# Function to check service status
check_service() {
    if pgrep -x "$1" > /dev/null; then
        echo "   ✅ $1 is running"
        return 0
    else
        echo "   ❌ $1 is not running"
        return 1
    fi
}

print_step "1" "System Check" "Verifying prerequisites"

# Check if we're in the right directory (support both .env and config.env layouts)
if [ -f "/workspace/config.env" ]; then
    echo "   ✅ Found configuration file: /workspace/config.env"
elif [ -f "/workspace/.env" ]; then
    echo "   ✅ Found configuration file: /workspace/.env"
else
    echo "❌ Error: No configuration file found. Expected /workspace/config.env or /workspace/.env"
    exit 1
fi

print_step "2" "Database Service" "Starting PostgreSQL"

# Check if PostgreSQL is running
if ! check_service "postgres"; then
    echo "   🔄 Starting PostgreSQL service..."
    service postgresql start
    sleep 3
    
    if check_service "postgres"; then
        echo "   ✅ PostgreSQL started successfully"
    else
        echo "   ❌ Failed to start PostgreSQL"
        exit 1
    fi
else
    echo "   ✅ PostgreSQL already running"
fi

print_step "3" "Database Connection" "Testing database connectivity"

# Test database connection
PGPASSWORD=sedi_password psql -h localhost -p 2036 -U sedi_user -d sedi_db -c "SELECT 1;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Database connection successful"
    
    # Check if tables exist
    TABLE_COUNT=$(PGPASSWORD=sedi_password psql -h localhost -p 2036 -U sedi_user -d sedi_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    echo "   ✅ Found $TABLE_COUNT database tables"
else
    echo "   ❌ Database connection failed - running database setup..."
    
    # Run database initialization if it fails
    if [ -f "/workspace/scripts/setup_postgres.sh" ]; then
        echo "   🔄 Running database setup..."
        bash /workspace/scripts/setup_postgres.sh
        sleep 2
    else
        echo "   ❌ Database setup script not found"
        exit 1
    fi
fi

print_step "4" "Python Environment" "Setting up Python dependencies"

# Check if running in container (no venv needed)
if [ -f "/.dockerenv" ] || [ "$CONTAINER" = "true" ]; then
    echo "   ✅ Running in container - using system Python"
else
    # Create virtual environment if it doesn't exist
    if [ ! -d "/workspace/venv" ]; then
        echo "   📦 Creating Python virtual environment..."
        python3 -m venv /workspace/venv
    fi
    
    echo "   🔄 Activating virtual environment..."
    source /workspace/venv/bin/activate
fi

# Install/update Python dependencies
echo "   📦 Installing Python dependencies..."
cd /workspace
pip install -r requirements.txt > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Python dependencies installed"
else
    echo "   ⚠️  Some Python dependencies may have issues (non-critical)"
fi

print_step "5" "Frontend Dependencies" "Checking Node.js setup"

# Check frontend dependencies (optional)
if [ -f "/workspace/frontend/package.json" ]; then
    echo "   📦 Frontend package.json found"
    cd /workspace/frontend
    
    # Check if node_modules exists
    if [ -d "node_modules" ]; then
        echo "   ✅ Frontend dependencies already installed"
    else
        echo "   📦 Installing frontend dependencies..."
        npm install > /dev/null 2>&1 || echo "   ⚠️  Node.js dependencies failed (non-critical - using static frontend)"
    fi
    cd /workspace
else
    echo "   ℹ️  No frontend package.json (using static frontend)"
fi

print_step "6" "Application Startup" "Starting FastAPI server"

# Set environment variables
export PYTHONPATH=/workspace:$PYTHONPATH

# Check if port 2035 is available
if lsof -i :2035 > /dev/null 2>&1; then
    echo "   ⚠️  Port 2035 is already in use"
    echo "   🔄 Attempting to stop existing service..."
    pkill -f "uvicorn.*main:app" 2>/dev/null || true
    sleep 2
fi

# Start the FastAPI application
echo "   🚀 Starting SEDI FastAPI server..."
echo "   📍 Server will be available at: http://localhost:2035/"
echo "   📊 API documentation at: http://localhost:2035/docs"
echo "   🧪 SSE test page at: http://localhost:2035/test_sse.html"
echo ""
echo "🎯 Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd /workspace/backend
uvicorn main:app --host 0.0.0.0 --port 2035 --reload
