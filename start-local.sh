#!/bin/bash

# Local development start script (without Docker)
# This requires Node.js, Python, PostgreSQL, and Redis to be installed locally

echo "Starting CourtListener Database Browser (Local Development Mode)"
echo ""
echo "This script starts the frontend and backend locally."
echo "You need PostgreSQL and Redis running separately."
echo ""

cd "$(dirname "$0")"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Start frontend
echo "Starting frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend in background
npm run dev &
FRONTEND_PID=$!
cd ..

# Start backend
echo "Starting backend..."
cd backend

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
    touch venv/.installed
fi

# Start backend
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

echo ""
echo "Services started!"
echo "Frontend PID: $FRONTEND_PID"
echo "Backend PID: $BACKEND_PID"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8001"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $FRONTEND_PID $BACKEND_PID 2>/dev/null; exit" INT TERM
wait

