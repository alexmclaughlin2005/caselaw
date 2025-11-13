#!/bin/bash

# Simple local development start script
# Runs frontend and backend without Docker

set -e

cd "$(dirname "$0")"

echo "🚀 Starting CourtListener Database Browser (Local Mode)"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    exit 1
fi
echo "✅ Node.js: $(node --version)"

if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

if ! command -v psql &> /dev/null; then
    echo "⚠️  Warning: PostgreSQL not found in PATH (may still work if running)"
else
    echo "✅ PostgreSQL: Found"
fi

echo ""

# Setup Frontend
echo "📦 Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies (this may take a few minutes)..."
    npm install
else
    echo "Frontend dependencies already installed"
fi

echo "Starting frontend dev server..."
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd ..

# Wait a moment for frontend to start
sleep 3

# Setup Backend
echo ""
echo "🐍 Setting up backend..."
cd backend

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "Installing backend dependencies (this may take a few minutes)..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/.installed
else
    echo "Backend dependencies already installed"
fi

# Check if PostgreSQL is accessible
echo ""
echo "Checking database connection..."
if python3 -c "import psycopg2; psycopg2.connect('postgresql://courtlistener:courtlistener@localhost:5432/courtlistener')" 2>/dev/null; then
    echo "✅ Database connection successful"
else
    echo "⚠️  Warning: Could not connect to database"
    echo "   Make sure PostgreSQL is running and database 'courtlistener' exists"
    echo "   You can create it with: createdb courtlistener"
fi

# Start backend
echo ""
echo "Starting backend server..."
export DATABASE_URL="postgresql://courtlistener:courtlistener@localhost:5432/courtlistener"
export REDIS_URL="redis://localhost:6379/0"
export ENVIRONMENT="development"
export CORS_ORIGINS='["http://localhost:3000","http://localhost:8001"]'

uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
cd ..

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Services started!"
echo ""
echo "📱 Frontend:  http://localhost:3000"
echo "🔧 Backend:   http://localhost:8001"
echo "📚 API Docs:  http://localhost:8001/docs"
echo ""
echo "📋 Logs:"
echo "   Frontend: tail -f frontend.log"
echo "   Backend:  tail -f backend.log"
echo ""
echo "⚠️  Note: Redis/Celery tasks won't work without Redis installed"
echo "   To install Redis: brew install redis && brew services start redis"
echo ""
echo "Press Ctrl+C to stop all services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $FRONTEND_PID $BACKEND_PID 2>/dev/null || true
    echo "Services stopped"
    exit 0
}

trap cleanup INT TERM

# Wait for processes
wait

