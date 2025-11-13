# Local Development Setup (Without Docker)

This guide helps you run the application locally without Docker, which is faster for development and testing.

## Prerequisites

You have most of what you need! Here's what's installed:
- ✅ Node.js v22.14.0
- ✅ Python 3.9.6
- ✅ PostgreSQL

## Missing: Redis (Optional)

Redis is only needed for background tasks (downloads/imports). The API and frontend will work without it.

**To install Redis (optional):**
```bash
brew install redis
brew services start redis
```

## Quick Start

### Step 1: Set up PostgreSQL Database

```bash
# Create the database (if it doesn't exist)
createdb courtlistener

# Or if you need to set a password:
psql postgres
CREATE DATABASE courtlistener;
CREATE USER courtlistener WITH PASSWORD 'courtlistener';
GRANT ALL PRIVILEGES ON DATABASE courtlistener TO courtlistener;
\q
```

### Step 2: Start the Application

```bash
cd "/Users/alexmclaughlin/Desktop/Cursor Projects/Court Listener"
./start-local-simple.sh
```

This will:
1. Install frontend dependencies (first time only)
2. Install backend dependencies (first time only)
3. Start the frontend on http://localhost:3000
4. Start the backend on http://localhost:8001

### Step 3: Create Database Schema

In a new terminal:

```bash
cd "/Users/alexmclaughlin/Desktop/Cursor Projects/Court Listener/backend"
source venv/bin/activate
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### Step 4: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

## Manual Start (Alternative)

If you prefer to start services manually:

### Terminal 1 - Frontend:
```bash
cd frontend
npm install  # First time only
npm run dev
```

### Terminal 2 - Backend:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # First time only
export DATABASE_URL="postgresql://courtlistener:courtlistener@localhost:5432/courtlistener"
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Troubleshooting

### Database Connection Error
```bash
# Check if PostgreSQL is running
pg_isready

# Create database if needed
createdb courtlistener

# Test connection
psql -U courtlistener -d courtlistener
```

### Port Already in Use
```bash
# Check what's using the port
lsof -i :3000  # Frontend
lsof -i :8001  # Backend

# Kill the process or change ports
```

### Frontend Can't Connect to Backend
- Check backend is running: http://localhost:8001/health
- Check browser console for CORS errors
- Verify `VITE_API_URL` in frontend/.env or vite.config.ts

## Benefits of Local Development

- ✅ Faster startup (no Docker overhead)
- ✅ Easier debugging (direct access to logs)
- ✅ Hot reload works better
- ✅ No need to rebuild containers
- ✅ Easier to modify and test

## Limitations Without Redis

- Background downloads won't work (can still download synchronously)
- Background imports won't work (can still import synchronously)
- Task status tracking won't work

For full functionality, install Redis:
```bash
brew install redis
brew services start redis
```

