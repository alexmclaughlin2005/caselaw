# Troubleshooting Guide

## Docker Not Found / Services Won't Start

### Issue: `docker: command not found` or `docker-compose: command not found`

**Solution 1: Install Docker Desktop**
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Install and start Docker Desktop
3. Wait for Docker Desktop to fully start (whale icon in menu bar)
4. Try running: `./start.sh` or `docker compose up -d`

**Solution 2: Add Docker to PATH**
If Docker is installed but not in PATH:
```bash
# Add Docker to PATH (add to ~/.zshrc or ~/.bash_profile)
export PATH="/usr/local/bin:$PATH"
```

**Solution 3: Use Docker Desktop GUI**
1. Open Docker Desktop
2. Go to Settings > Resources > File Sharing
3. Add the project directory: `/Users/alexmclaughlin/Desktop/Cursor Projects/Court Listener`
4. Use Docker Desktop's terminal or run commands from there

### Issue: Docker is running but services won't start

**Check Docker is running:**
```bash
docker ps
# Should show running containers or empty list (not an error)
```

**Check ports are available:**
```bash
# Check if ports are in use
lsof -i :3000  # Frontend
lsof -i :8001  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill processes if needed (replace PID)
kill -9 <PID>
```

**Start services manually:**
```bash
cd "/Users/alexmclaughlin/Desktop/Cursor Projects/Court Listener"

# Try docker compose (newer)
docker compose up -d

# Or docker-compose (older)
docker-compose up -d
```

### Issue: Frontend won't load at http://localhost:3000

**Check frontend container:**
```bash
docker compose ps frontend
docker compose logs frontend
```

**Common issues:**
1. **Port already in use**: Another app is using port 3000
   ```bash
   lsof -i :3000
   # Kill the process or change FRONTEND_PORT in .env
   ```

2. **Frontend build failed**: Check logs
   ```bash
   docker compose logs frontend
   ```

3. **Node modules not installed**: Rebuild container
   ```bash
   docker compose build frontend
   docker compose up -d frontend
   ```

4. **Vite dev server not starting**: Check vite.config.ts
   - Ensure `host: '0.0.0.0'` is set
   - Check port is 3000

**Restart frontend:**
```bash
docker compose restart frontend
docker compose logs -f frontend
```

### Issue: Backend won't start

**Check backend container:**
```bash
docker compose ps backend
docker compose logs backend
```

**Common issues:**
1. **Database connection error**: PostgreSQL not ready
   ```bash
   docker compose ps postgres
   docker compose logs postgres
   # Wait for postgres to be healthy, then restart backend
   docker compose restart backend
   ```

2. **Python dependencies missing**: Rebuild container
   ```bash
   docker compose build backend
   docker compose up -d backend
   ```

3. **Port 8001 in use**: Check and kill process
   ```bash
   lsof -i :8001
   ```

### Issue: Can't access API from frontend

**Check CORS settings:**
- Backend should allow `http://localhost:3000`
- Check `backend/app/core/config.py`:
  ```python
  CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8001"]
  ```

**Check API URL:**
- Frontend uses `VITE_API_URL` from environment
- Default should be `http://localhost:8001`
- Check browser console for CORS errors

**Test API directly:**
```bash
curl http://localhost:8001/health
# Should return: {"status":"healthy","service":"courtlistener-api"}
```

### Issue: Database migration errors

**Check database exists:**
```bash
docker compose exec postgres psql -U courtlistener -l
```

**Create migration:**
```bash
docker compose exec backend alembic revision --autogenerate -m "Initial schema"
docker compose exec backend alembic upgrade head
```

**Reset database (WARNING: deletes all data):**
```bash
docker compose down -v  # Removes volumes
docker compose up -d postgres
# Wait for postgres to start
docker compose exec backend alembic upgrade head
```

## Running Without Docker (Local Development)

If Docker isn't working, you can run locally:

### Prerequisites:
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Redis

### Steps:

1. **Start PostgreSQL and Redis** (using Homebrew or your preferred method)

2. **Start Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. **Start Frontend (new terminal):**
```bash
cd frontend
npm install
npm run dev
```

4. **Set up database:**
```bash
# In backend directory with venv activated
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

## Getting Help

1. **Check all logs:**
```bash
docker compose logs
```

2. **Check specific service:**
```bash
docker compose logs backend
docker compose logs frontend
docker compose logs postgres
```

3. **Restart everything:**
```bash
docker compose down
docker compose up -d
```

4. **Complete reset (WARNING: deletes data):**
```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

