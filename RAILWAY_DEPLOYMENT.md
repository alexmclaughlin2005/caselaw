# Railway Deployment Instructions

## Current Status
- **Backend**: DOWN (404) - Service crashed during parallel import
- **Database**: Railway PostgreSQL - 0 records
- **Volume Activity**: 15GB downloaded but not imported

## Root Cause Analysis
1. Downloads went to ephemeral container filesystem `/app/data` instead of Railway volume
2. Threading approach may have caused Railway to kill the process
3. No persistent volume mount configured in Railway dashboard

---

## Step 1: Railway Dashboard Setup

### 1.1 Create Volume for Data Storage
In the Railway dashboard:
1. Go to your project: **CourtListener Database Browser**
2. Click on the backend service
3. Go to **Variables** tab
4. Add a new volume:
   - **Mount Path**: `/data`
   - **Size**: 150GB (to accommodate all CSV files + decompression)
   - **Name**: `courtlistener-data`

### 1.2 Configure Environment Variables
Set these variables in Railway dashboard:
```env
DATABASE_URL=<your-railway-postgres-url>
DATA_DIR=/data
PORT=8000
LOG_LEVEL=INFO
RAILWAY_ENVIRONMENT=production
```

### 1.3 Verify PostgreSQL Service
Ensure PostgreSQL service is running:
- Database: Railway PostgreSQL
- Check connection string is set
- Verify alembic migrations have run

---

## Step 2: Redeploy Backend

### 2.1 Commit Configuration Changes
```bash
git add backend/app/core/config.py
git add backend/app/api/routes/data_management.py
git commit -m "Fix: Use Railway volume mount for data downloads

- Change DATA_DIR from ./data to /data
- Update parallel import to use configurable DATA_DIR
- Ensure data directory creation before downloads"
git push origin main
```

### 2.2 Railway Will Auto-Deploy
- Railway detects the push and redeploys automatically
- Monitor deployment logs in Railway dashboard
- Wait for "Deployment successful" message

### 2.3 Verify Backend is Running
```bash
# Check health endpoint
curl https://courtlistener-database-browser-production.up.railway.app/health

# Expected response:
# {"status":"healthy","database":"connected"}
```

---

## Step 3: Trigger Parallel Import

### 3.1 Start the Import Process
```bash
# Trigger parallel download + import
curl -X POST https://courtlistener-database-browser-production.up.railway.app/api/data/import-parallel

# Expected response:
# {
#   "status": "started",
#   "message": "Parallel import from S3 started for date 2025-10-31",
#   "date": "2025-10-31",
#   "tables": ["search_docket", "search_opinioncluster", "search_opinionscited", "search_parenthetical"]
# }
```

### 3.2 Monitor Import Progress

**Option A: Check Railway Logs**
1. Railway Dashboard → Backend Service → Logs
2. Look for:
   ```
   [search_docket] Starting download from S3: dockets-2025-10-31.csv.bz2
   [search_docket] Download complete: /data/search_docket-2025-10-31.csv
   [search_docket] File size: 17.50 GB
   [search_docket] Starting import to database
   [search_docket] ✓ Import complete: 70,000,000 rows
   ```

**Option B: Use Monitoring Endpoints**
```bash
# Get current record counts
curl https://courtlistener-database-browser-production.up.railway.app/api/monitoring/database/counts

# Check import progress percentage
curl https://courtlistener-database-browser-production.up.railway.app/api/monitoring/import/progress

# View database activity
curl https://courtlistener-database-browser-production.up.railway.app/api/monitoring/database/activity
```

**Option C: Use Frontend Monitor**
- Open: https://caselaw-seven.vercel.app/monitor
- Real-time dashboard with 5-second auto-refresh
- Shows per-table progress bars

---

## Step 4: Expected Timeline & Results

### Download + Import Times (Parallel)
With 4 threads running simultaneously on Railway:

| Table | CSV Size (compressed) | Rows | Est. Download | Est. Import | Total |
|-------|----------------------|------|---------------|-------------|-------|
| search_docket | 3.5 GB | 70M | 5-10 min | 20-40 min | 30-50 min |
| search_opinionscited | 4.8 GB | 76M | 7-12 min | 25-50 min | 35-60 min |
| search_opinioncluster | 4.5 GB | 6M | 6-11 min | 10-20 min | 20-30 min |
| search_parenthetical | 1.2 GB | 6M | 2-5 min | 10-15 min | 15-20 min |

**Total Parallel Time**: 35-60 minutes (since all run concurrently)

### Expected Results
```sql
-- After completion, verify counts:
SELECT 'search_docket' as table, COUNT(*) FROM search_docket;
-- Expected: ~70,000,000

SELECT 'search_opinionscited' as table, COUNT(*) FROM search_opinionscited;
-- Expected: ~76,000,000

SELECT 'search_opinioncluster' as table, COUNT(*) FROM search_opinioncluster;
-- Expected: ~6,000,000

SELECT 'search_parenthetical' as table, COUNT(*) FROM search_parenthetical;
-- Expected: ~6,000,000
```

---

## Step 5: Troubleshooting

### If Import Fails or Hangs

**Check Railway Logs**
```bash
# Look for errors in Railway dashboard logs
# Common issues:
# - Out of memory (OOMKilled)
# - Disk space full
# - Database connection timeout
# - Threading issues
```

**Restart the Service**
1. Railway Dashboard → Backend Service
2. Click "Restart"
3. Wait for service to come back online
4. Re-trigger import

**Check Volume Usage**
```bash
# In Railway shell (if available)
df -h /data

# Expected during download phase: ~77GB used
# Expected after decompression: ~0GB (CSVs deleted after import)
```

### If Backend Won't Start (404)

**Check Migrations**
```bash
# Railway logs should show:
# "Running database migrations..."
# "Starting uvicorn server..."

# If migrations fail:
# 1. Check DATABASE_URL is set correctly
# 2. Check PostgreSQL service is running
# 3. Check for alembic errors in logs
```

**Check Port Configuration**
- Railway sets `PORT` env var automatically
- Backend should use `--port ${PORT:-8000}`
- Verify in [Dockerfile:27](Dockerfile#L27)

### If Downloads Fail

**Check S3 Access**
```bash
# Test S3 connectivity from Railway shell
curl -I https://com-courtlistener-storage.s3.us-west-2.amazonaws.com/bulk-data/dockets-2025-10-31.csv.bz2

# Should return 200 OK
```

**Check Volume Mount**
```bash
# Verify /data is writable
# Railway shell:
touch /data/test.txt && ls -la /data/test.txt && rm /data/test.txt
```

---

## Step 6: Verification Checklist

After successful deployment and import:

- [ ] Backend health check returns `{"status":"healthy","database":"connected"}`
- [ ] Railway volume shows ~77GB used during downloads
- [ ] Database contains all 4 tables with expected row counts
- [ ] Frontend can query dockets: `GET /api/dockets?limit=10`
- [ ] Frontend can query opinions: `GET /api/opinions?limit=10`
- [ ] Railway logs show no errors
- [ ] Import completion logged: `PARALLEL IMPORT COMPLETE`

---

## Step 7: Cost Monitoring

### Railway Usage
Monitor in Railway dashboard:
- **Database**: ~50-60GB storage ($5-6/month)
- **Volume**: ~0-1GB after import ($0-1/month, CSVs deleted)
- **Compute**: Check CPU/RAM usage during steady state
- **Network**: ~20GB download from S3 (one-time)

### Optimization Tips
1. After import completes, CSVs are deleted automatically
2. Scale down compute resources if needed
3. Set up spending alerts in Railway
4. Consider backing up database after import

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Railway Environment                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐         ┌──────────────────┐            │
│  │ Backend Service│────────▶│ PostgreSQL DB    │            │
│  │  FastAPI       │         │  (managed)       │            │
│  │  Port: $PORT   │         │  158M rows total │            │
│  └────────┬───────┘         └──────────────────┘            │
│           │                                                   │
│           │ mounts                                            │
│           ▼                                                   │
│  ┌────────────────┐                                          │
│  │ Volume: /data  │                                          │
│  │ 150GB capacity │                                          │
│  │ (CSVs stored)  │                                          │
│  └────────────────┘                                          │
│           ▲                                                   │
│           │ downloads                                         │
│           │                                                   │
└───────────┼───────────────────────────────────────────────────┘
            │
            │ HTTPS
            │
    ┌───────▼────────┐
    │ CourtListener  │
    │ S3 Bucket      │
    │ (public read)  │
    └────────────────┘
```

---

## Next Actions

1. **Immediate**: Check Railway dashboard for volume configuration
2. **If no volume**: Create 150GB volume mounted at `/data`
3. **After volume setup**: Redeploy from latest commit
4. **When backend is healthy**: Trigger `/api/data/import-parallel`
5. **Monitor**: Use frontend dashboard or Railway logs
6. **Verify**: Check record counts after completion (30-90 min)

---

**Last Updated**: 2025-11-13
**Status**: Ready for deployment
