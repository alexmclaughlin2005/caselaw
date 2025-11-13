# Setup Guide

## Prerequisites

- Docker Desktop installed and running
- Git (optional, for version control)

## Quick Start

1. **Clone or navigate to the project directory**:
   ```bash
   cd "Court Listener"
   ```

2. **Create environment file** (if not exists):
   ```bash
   cp .env.example .env
   # Edit .env if needed (defaults should work)
   ```

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to start** (about 30 seconds):
   ```bash
   # Check logs
   docker-compose logs -f
   ```

5. **Create database migration** (first time only):
   ```bash
   docker-compose exec backend alembic revision --autogenerate -m "Initial schema"
   docker-compose exec backend alembic upgrade head
   ```

6. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - API Documentation: http://localhost:8001/docs

## Using the Data Management UI

1. **Navigate to Data Management**:
   - Go to http://localhost:3000
   - Click "Go to Data Management" or navigate to `/data`

2. **Download a Dataset**:
   - Select a date from the "Available Datasets" list
   - Click "Download Dataset"
   - Watch the progress bar as files download
   - Wait for download to complete

3. **Import Data**:
   - After download completes, click "Import Dataset"
   - Watch the progress as tables are imported
   - Check the database status to see imported records

4. **View Database Status**:
   - The top card shows current database statistics
   - Record counts update automatically after import

## Troubleshooting

### Services won't start
```bash
# Check if ports are in use
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Start fresh
docker-compose up -d
```

### Frontend can't connect to backend
- Check that backend is running: `docker-compose ps`
- Check backend logs: `docker-compose logs backend`
- Verify CORS settings in `backend/app/core/config.py`

### Database connection errors
- Check PostgreSQL is running: `docker-compose ps postgres`
- Check database logs: `docker-compose logs postgres`
- Verify DATABASE_URL in `.env` matches docker-compose.yml

### Migration errors
- Ensure models are imported in `backend/alembic/env.py`
- Check database exists: `docker-compose exec postgres psql -U courtlistener -l`
- Try recreating migration: `docker-compose exec backend alembic revision --autogenerate -m "Initial schema"`

### Download/Import not working
- Check Celery worker is running: `docker-compose ps celery-worker`
- Check Celery logs: `docker-compose logs celery-worker`
- Check Redis is running: `docker-compose ps redis`

## Development

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery-worker
```

### Restart a service
```bash
docker-compose restart backend
docker-compose restart frontend
```

### Access containers
```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend bash

# PostgreSQL shell
docker-compose exec postgres psql -U courtlistener -d courtlistener
```

### Run migrations
```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

## Environment Variables

Key environment variables (in `.env`):

- `POSTGRES_USER` - Database user (default: courtlistener)
- `POSTGRES_PASSWORD` - Database password (default: courtlistener)
- `POSTGRES_DB` - Database name (default: courtlistener)
- `VITE_API_URL` - Backend API URL (default: http://localhost:8001)

## Next Steps

After setup:
1. Download a dataset via the UI
2. Import the dataset
3. Verify data in the database
4. Proceed to Phase 4 (API endpoints for browsing data)

