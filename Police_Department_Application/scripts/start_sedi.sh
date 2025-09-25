#!/bin/bash
set -e

echo "🚔 Starting Police SEDI Application..."

# Check if PostgreSQL is running
if ! pgrep -x "postgres" > /dev/null; then
    echo "📊 Starting PostgreSQL..."
    service postgresql start
    sleep 3
fi

# Test database connection
echo "🔗 Testing database connection..."
PGPASSWORD=sedi_password psql -h localhost -p 2036 -U sedi_user -d sedi_db -c "SELECT 1;" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    exit 1
fi

# Install Python dependencies if not already installed
if [ ! -d "/workspace/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python -m venv /workspace/venv
fi

source /workspace/venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install -r /workspace/requirements.txt

# Install Node.js dependencies for frontend (if package.json exists)
if [ -f "/workspace/frontend/package.json" ]; then
    echo "🎨 Installing frontend dependencies..."
    cd /workspace/frontend
    npm install
    cd /workspace
fi

echo "🚀 Starting SEDI FastAPI server on port 2035..."
cd /workspace/backend
export PYTHONPATH=/workspace:$PYTHONPATH
uvicorn main:app --host 0.0.0.0 --port 2035 --reload
