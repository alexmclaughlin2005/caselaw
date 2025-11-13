# Railway Migration Plan - Court Listener Backend

## Executive Summary

**Objective**: Migrate backend processing and PostgreSQL database from local Docker to Railway platform to solve disk space constraints and improve reliability.

**Current State**: (NO LONGER DOING LOCAL TO RAILWAY PUSH!!)
- Local PostgreSQL with 43GB data (3 tables imported)
- 77GB CSV files on local machine
- 100% disk capacity (1.2GB free)
- Import process failing due to memory/disk constraints

**Target State**:
- Railway-hosted PostgreSQL with all 4 tables
- Backend API deployed on Railway
- GitHub integration for CI/CD
- Local development environment connecting to Railway

**Timeline**: 2-3 days
**Estimated Cost**: $20-50/month on Railway

---

## Phase 1: Railway Setup & Configuration (1-2 hours)

### Task 1.1: Create Railway Project
- [ ] Log into Railway dashboard
- [ ] Create new project: "CourtListener Backend"
- [ ] Connect GitHub repository

### Task 1.2: Provision PostgreSQL Database
- [ ] Add PostgreSQL service to project
- [ ] Select appropriate plan:
  - **Recommended**: 8GB RAM, 50GB storage minimum
  - Reason: Need headroom for 74M row imports
- [ ] Note connection credentials:
  - `PGHOST`
  - `PGPORT`
  - `PGUSER`
  - `PGPASSWORD`
  - `PGDATABASE`
  - Public connection URL

### Task 1.3: Configure Environment Variables
Update Railway project variables:
```env
# Database
DATABASE_URL=postgresql://user:pass@host:port/db
POSTGRES_HOST=xxxxx.railway.app
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=xxxxx
POSTGRES_DB=railway

# App Config
DATA_DIR=/app/data
LOG_LEVEL=INFO

# Redis (if needed later)
REDIS_URL=redis://...

# AWS (for S3 downloads)
AWS_ACCESS_KEY_ID=xxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
```

### Task 1.4: Update Local Configuration
Files to update:
- `backend/.env` - Add Railway database credentials
- `backend/app/core/config.py` - Verify settings class reads env vars correctly
- `docker-compose.yml` - Comment out local postgres service (keep for dev backup)

---

## Phase 2: Database Migration (2-3 hours)

### Task 2.1: Apply Database Schema to Railway
```bash
# From local machine
cd backend
alembic upgrade head --sql > railway_migrations.sql

# Or run migrations directly against Railway
export DATABASE_URL="postgresql://user:pass@railway.app:port/db"
alembic upgrade head
```

**Verification**:
- [ ] All tables created
- [ ] Alembic version matches local
- [ ] Indexes created

### Task 2.2: Decision Point - Data Migration Strategy

#### Option A: Fresh Import (RECOMMENDED)
**Advantages**:
- Clean slate
- Railway has space for full import
- Can import all 4 tables including opinioncluster
- Faster than exporting/importing 43GB

**Steps**:
1. Upload CSV files to Railway volume or S3
2. Run imports directly on Railway
3. Monitor with Railway logs

#### Option B: Migrate Existing Data
**Advantages**:
- Keep 70M docket + 76M opinionscited records

**Steps**:
1. Export local data:
   ```bash
   docker exec courtlistener-postgres pg_dump -U courtlistener -d courtlistener \
     --data-only --table=search_docket --table=search_opinionscited \
     --table=search_parenthetical > backup.sql
   ```
2. Restore to Railway:
   ```bash
   psql $RAILWAY_DATABASE_URL < backup.sql
   ```

**Disadvantages**:
- Need 43GB disk space for export (you don't have)
- Slow transfer over network

**DECISION**: Go with Option A (Fresh Import)

### Task 2.3: Upload CSV Files to Railway

**Method 1: Railway Volume Mount**
```bash
# Railway CLI
railway volume create courtlistener-data 100GB
railway volume mount courtlistener-data /app/data

# Upload CSVs
railway run scp local/search_docket-2025-10-31.csv /app/data/
railway run scp local/search_opinionscited-2025-10-31.csv /app/data/
railway run scp local/search_opinioncluster-2025-10-31.csv /app/data/
railway run scp local/search_parenthetical-2025-10-31.csv /app/data/
```

**Method 2: S3 Download (FASTER - RECOMMENDED)**
- CSVs already available in CourtListener's public S3
- Download directly to Railway from S3
- No need to upload from local machine
- Saves bandwidth and time

---

## Phase 3: Deploy Backend Application (2-3 hours)

### Task 3.1: Prepare Backend for Railway Deployment

**Update Dockerfile for Railway**:
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Railway uses PORT environment variable
ENV PORT=8000

# Run migrations and start server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Update docker-compose.yml**:
```yaml
# For local development only
services:
  # Comment out postgres - use Railway
  # postgres:
  #   ...

  backend:
    build: ./backend
    environment:
      - DATABASE_URL=${RAILWAY_DATABASE_URL}
    ports:
      - "8000:8000"
    depends_on: []  # Remove postgres dependency
```

### Task 3.2: Create Railway Service for Backend API

**Option A: Deploy from GitHub (RECOMMENDED)**
1. Railway dashboard → "New Service" → "GitHub Repo"
2. Select repository
3. Set root directory: `/backend`
4. Railway auto-detects Dockerfile
5. Set environment variables from Phase 1.3

**Option B: Deploy with Railway CLI**
```bash
cd backend
railway link  # Link to project
railway up    # Deploy
```

### Task 3.3: Create Railway Service for Worker

**Purpose**: Run data import jobs separately from API

**Create separate service**:
1. Railway dashboard → "New Service" → Same GitHub repo
2. Root directory: `/backend`
3. Override start command:
   ```bash
   celery -A app.celery_app worker --loglevel=info
   ```
4. Set same environment variables as backend

**Alternative**: Use Railway Cron Jobs for scheduled imports

### Task 3.4: Verify Deployment
- [ ] Backend API accessible at Railway URL
- [ ] Health check endpoint responds: `GET /health`
- [ ] Database connection successful
- [ ] Logs show no errors

---

## Phase 4: Data Import on Railway (4-8 hours)

### Task 4.1: Set Up Import Environment

**Access Railway shell**:
```bash
railway run bash

# Or through Railway dashboard → Service → Shell
```

**Install dependencies** (if not in Docker image):
```bash
pip install pandas numpy
```

### Task 4.2: Download CSVs from S3

**Option A: Use existing downloader**:
```python
# Railway shell
python3 -c "
from app.services.s3_downloader import CourtListenerDownloader
from pathlib import Path

downloader = CourtListenerDownloader()

# Download all CSVs
files = [
    'bulk-data/search_docket-2025-10-31.csv.bz2',
    'bulk-data/search_opinionscited-2025-10-31.csv.bz2',
    'bulk-data/opinion-clusters-2025-10-31.csv.bz2',
    'bulk-data/search_parenthetical-2025-10-31.csv.bz2',
]

for file in files:
    print(f'Downloading {file}...')
    downloader.download_file(file)
    print('Done!')
"
```

**Option B: Direct wget/curl**:
```bash
cd /app/data
wget https://com-courtlistener-storage.s3.us-west-2.amazonaws.com/bulk-data/search_docket-2025-10-31.csv.bz2
bunzip2 search_docket-2025-10-31.csv.bz2
# Repeat for other files
```

### Task 4.3: Run Imports

**Import script for Railway**:
```python
# /app/import_all_tables.py
from pathlib import Path
from app.services.data_importer import DataImporter
from app.core.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def import_all_tables():
    importer = DataImporter(data_dir=Path('/app/data'))
    session = SessionLocal()

    tables = [
        ('search_docket', 'search_docket-2025-10-31.csv', 'import_csv'),
        ('search_opinionscited', 'search_opinionscited-2025-10-31.csv', 'import_csv'),
        ('search_parenthetical', 'search_parenthetical-2025-10-31.csv', 'import_csv'),
        ('search_opinioncluster', 'search_opinioncluster-2025-10-31.csv', 'import_csv_pandas'),
    ]

    for table_name, csv_file, method in tables:
        try:
            logger.info(f"=" * 80)
            logger.info(f"Starting import: {table_name}")
            logger.info(f"=" * 80)

            csv_path = Path(f'/app/data/{csv_file}')

            if method == 'import_csv_pandas':
                row_count = importer.import_csv_pandas(table_name, csv_path, session)
            else:
                row_count = importer.import_csv(table_name, csv_path, session)

            logger.info(f"✓ {table_name} completed: {row_count:,} rows")

        except Exception as e:
            logger.error(f"✗ {table_name} failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            session.rollback()

    session.close()
    logger.info("=" * 80)
    logger.info("All imports completed!")
    logger.info("=" * 80)

if __name__ == "__main__":
    import_all_tables()
```

**Run import on Railway**:
```bash
# Railway shell
python3 /app/import_all_tables.py > /tmp/import_log.txt 2>&1 &

# Monitor progress
tail -f /tmp/import_log.txt
```

**Or use Railway worker service**:
```bash
# Trigger via API or Celery task
railway run python3 -c "
from app.tasks.import_tasks import import_all_tables_task
import_all_tables_task.delay()
"
```

### Task 4.4: Monitor Import Progress

**Check database counts**:
```bash
railway run psql $DATABASE_URL -c "
SELECT
    'search_docket' as table, COUNT(*) FROM search_docket
UNION ALL
SELECT 'search_opinionscited', COUNT(*) FROM search_opinionscited
UNION ALL
SELECT 'search_parenthetical', COUNT(*) FROM search_parenthetical
UNION ALL
SELECT 'search_opinioncluster', COUNT(*) FROM search_opinioncluster;
"
```

**Expected counts**:
- search_docket: ~70M rows
- search_opinionscited: ~76M rows
- search_parenthetical: ~6M rows
- search_opinioncluster: ~75M rows

**Estimated time on Railway (8GB RAM)**:
- search_docket: 1-2 hours
- search_opinionscited: 1-2 hours
- search_parenthetical: 20 minutes
- search_opinioncluster: 2-3 hours (pandas parser)
- **Total**: 4-8 hours

---

## Phase 5: Update Application Configuration (30 mins)

### Task 5.1: Update Backend Configuration Files

**backend/app/core/config.py**:
```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # Railway-specific
    RAILWAY_ENVIRONMENT: str = Field("development", env="RAILWAY_ENVIRONMENT")
    PORT: int = Field(8000, env="PORT")

    # Data directory (Railway volume or /tmp)
    DATA_DIR: str = Field("/app/data", env="DATA_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = True
```

**backend/app/main.py**:
```python
# Add Railway health check
@app.get("/health")
async def health_check():
    """Railway health check endpoint"""
    try:
        # Test DB connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500
```

### Task 5.2: Update Local Development Setup

**backend/.env.example**:
```env
# For local development - copy to .env
DATABASE_URL=postgresql://user:pass@localhost:5432/courtlistener

# For Railway connection from local
# DATABASE_URL=postgresql://postgres:xxx@xxx.railway.app:5432/railway
```

**README.md** - Add Railway deployment section:
```markdown
## Deployment

### Railway

1. Database: Hosted on Railway PostgreSQL
2. Backend API: Deployed from GitHub
3. Connection: Set DATABASE_URL in Railway environment variables

### Local Development

Use local PostgreSQL or connect to Railway:
```bash
export DATABASE_URL="railway_connection_string"
python -m uvicorn app.main:app --reload
```
```

---

## Phase 6: Testing & Verification (1 hour)

### Task 6.1: API Testing

**Test endpoints**:
```bash
# Health check
curl https://your-app.railway.app/health

# Test docket search
curl https://your-app.railway.app/api/dockets?limit=10

# Test opinion search
curl https://your-app.railway.app/api/opinions?limit=10
```

### Task 6.2: Database Verification

**Row counts**:
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Sample data checks**:
```sql
-- Check for NULL in critical fields
SELECT COUNT(*) as total,
       COUNT(case_name) as has_case_name,
       COUNT(court_id) as has_court
FROM search_docket
LIMIT 1;

-- Check opinion cluster data quality
SELECT COUNT(*) as total,
       COUNT(headmatter) as has_headmatter,
       COUNT(disposition) as has_disposition
FROM search_opinioncluster
LIMIT 1;
```

### Task 6.3: Performance Testing

**Query performance**:
```sql
-- Test index usage
EXPLAIN ANALYZE
SELECT * FROM search_docket
WHERE court_id = 'ca9'
LIMIT 100;

-- Test join performance
EXPLAIN ANALYZE
SELECT d.case_name, oc.date_filed
FROM search_docket d
JOIN search_opinioncluster oc ON d.id = oc.docket_id
LIMIT 100;
```

---

## Phase 7: Cleanup & Optimization (1 hour)

### Task 7.1: Local Cleanup

**Free up disk space**:
```bash
# Stop local imports
docker exec courtlistener-celery-worker pkill -f python3

# Delete CSV files
docker exec courtlistener-celery-worker rm -rf /app/data/*.csv

# Verify space freed
df -h
```

**Expected space freed**: ~77GB

### Task 7.2: Railway Optimization

**Database**:
- [ ] Create additional indexes for common queries
- [ ] Set up automated backups (Railway UI)
- [ ] Configure connection pooling if needed

**Application**:
- [ ] Set up Railway metrics/monitoring
- [ ] Configure auto-scaling if needed
- [ ] Set up log retention

### Task 7.3: Cost Optimization

**Review Railway usage**:
- Database size: ~50GB expected
- CPU/RAM usage during imports vs steady state
- Network egress

**Recommendations**:
- Scale down after imports complete
- Use Railway's usage-based pricing
- Set up spending alerts

---

## Phase 8: CI/CD Setup (1 hour)

### Task 8.1: GitHub Actions for Railway Deployment

**Create `.github/workflows/railway-deploy.yml`**:
```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### Task 8.2: Set Up GitHub Secrets

Add to repository secrets:
- `RAILWAY_TOKEN` - From Railway dashboard

### Task 8.3: Configure Railway Auto-Deploy

Railway dashboard:
1. Settings → Deployments
2. Enable "Auto Deploy" from main branch
3. Configure deployment triggers

---

## Phase 9: Documentation (30 mins)

### Task 9.1: Update Project Documentation

**Create `DEPLOYMENT.md`**:
- Railway setup instructions
- Environment variables reference
- Deployment process
- Rollback procedures

**Create `RAILWAY_OPERATIONS.md`**:
- How to run imports
- How to access Railway shell
- Monitoring and logging
- Backup/restore procedures

### Task 9.2: Update README.md

Add sections:
- Railway deployment status badge
- Production vs development environments
- Connection instructions

---

## Rollback Plan

If Railway migration fails, rollback to local:

1. **Restore local database**:
   ```bash
   docker-compose up -d postgres
   ```

2. **Revert configuration**:
   ```bash
   git checkout backend/.env
   git checkout backend/app/core/config.py
   ```

3. **Restart local services**:
   ```bash
   docker-compose up -d
   ```

---

## Success Criteria

- [ ] Railway PostgreSQL database running with all 4 tables
- [ ] All expected row counts present (70M+ docket, 76M+ opinionscited, 75M+ opinioncluster, 6M+ parenthetical)
- [ ] Backend API deployed and accessible via Railway URL
- [ ] API responds to health checks
- [ ] Database queries performing well (< 1s for simple queries)
- [ ] Local machine disk space freed (77GB+)
- [ ] GitHub CI/CD pipeline working
- [ ] Documentation updated
- [ ] Cost under $50/month

---

## Cost Estimates

### Railway Pricing (as of 2024)

**PostgreSQL**:
- Hobby: $5/month (500MB, not sufficient)
- Pro: $10/month + usage ($0.10/GB, ~$5 for 50GB) = ~$15/month
- **Recommended**: Pro plan with 50-100GB storage

**Backend API Service**:
- Starter: $5/month (512MB RAM)
- Pro: $10/month + usage (8GB RAM during imports)
- **Recommended**: Start with Starter, scale to Pro during imports

**Worker Service** (optional):
- Starter: $5/month

**Total Estimated Cost**:
- During imports: $40-50/month (scaled up)
- Steady state: $20-30/month (scaled down)

---

## Timeline

| Phase | Task | Duration | Dependencies |
|-------|------|----------|--------------|
| 1 | Railway Setup | 1-2 hours | None |
| 2 | Database Migration | 2-3 hours | Phase 1 |
| 3 | Backend Deployment | 2-3 hours | Phase 1, 2 |
| 4 | Data Import | 4-8 hours | Phase 2, 3 |
| 5 | Configuration Updates | 30 mins | Phase 3 |
| 6 | Testing | 1 hour | Phase 4 |
| 7 | Cleanup | 1 hour | Phase 6 |
| 8 | CI/CD Setup | 1 hour | Phase 3 |
| 9 | Documentation | 30 mins | All |

**Total Time**: 13-20 hours (2-3 days elapsed, can run imports overnight)

---

## Next Steps

1. **Immediate**: Create Railway account and project
2. **Day 1**: Complete Phases 1-3 (setup, schema, deployment)
3. **Day 2**: Run data imports (Phase 4) - can run overnight
4. **Day 3**: Testing, cleanup, documentation (Phases 5-9)

---

## Notes

- Railway has generous free tier for testing
- Can run imports overnight to save time
- Keep local Docker setup for development
- Railway provides automatic SSL, monitoring, logging
- Database backups handled by Railway
- Easy to scale resources up/down as needed

---

**Last Updated**: 2025-11-13
**Status**: Ready for execution
