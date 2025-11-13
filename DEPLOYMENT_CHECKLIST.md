# Deployment Checklist

## Status: In Progress

### ✅ Completed
- [x] Git repository initialized and pushed to GitHub
- [x] Railway PostgreSQL database created
- [x] Backend .env file configured
- [x] Config.py updated for Railway compatibility
- [x] Railway backend service deployed from GitHub
- [x] Railway environment variables configured
- [x] Railway volume created and mounted at /app/data

### 🔄 In Progress - Verify Railway Deployment

#### Step 1: Deploy Backend to Railway ✅
1. Go to: https://railway.app/dashboard
2. Click **"+ New"** → **"Deploy from GitHub repo"**
3. Select repository: **`alexmclaughlin2005/caselaw`**
4. Railway will detect Dockerfile automatically
5. Click **"Deploy"**

#### Step 2: Link PostgreSQL to Backend ✅
1. In Railway dashboard, click on your backend service
2. Go to **"Variables"** tab
3. Click **"+ New Variable"** → **"Add Reference"**
4. Select your **PostgreSQL** database
5. This shares `DATABASE_URL` automatically

#### Step 3: Add Additional Environment Variables ✅
In backend service → **Variables** tab, add:

```env
DATA_DIR=/app/data
LOG_LEVEL=INFO
ENVIRONMENT=production
ALLOWED_ORIGINS=http://localhost:3000
PORT=8000
S3_BUCKET_NAME=com-courtlistener-storage
S3_PREFIX=bulk-data/
```

#### Step 4: Create Railway Volume ✅
1. In backend service, go to **"Settings"** or **"Volumes"** tab
2. Click **"+ New Volume"**
3. Configure:
   - **Mount Path**: `/app/data`
   - **Size**: 10-20 GB (expandable later)
4. Click **"Create"**
5. Service will automatically redeploy with volume attached

#### Step 5: Wait for Deployment
- Railway will build Docker image (~2-3 minutes)
- Run migrations automatically (via railway.json startCommand)
- Start the FastAPI server
- You'll get a URL like: `https://caselaw-production.up.railway.app`

#### Step 6: Verify Backend 🔄 CURRENT STEP
Once deployed, test:
```bash
curl https://your-railway-url.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### 🔄 Next - Vercel Frontend

#### Step 1: Import Project
1. Go to: https://vercel.com/dashboard
2. Click **"Add New Project"**
3. Import: **`alexmclaughlin2005/caselaw`**

#### Step 2: Configure Build Settings
- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

#### Step 3: Add Environment Variable
```env
VITE_API_URL=https://your-railway-url.railway.app
```
(Replace with actual Railway URL from Step 4 above)

#### Step 4: Deploy
Click **"Deploy"** - takes ~1-2 minutes

#### Step 5: Update CORS
Once Vercel deploys, you'll get a URL like: `https://caselaw-xyz.vercel.app`

Go back to Railway → Backend service → Variables:
```env
ALLOWED_ORIGINS=https://caselaw-xyz.vercel.app,http://localhost:3000
```

---

### 🔄 Final - Import Data to Railway

#### Option A: Railway Shell (Recommended)
1. Railway dashboard → Backend service
2. Click **"..."** → **"Shell"**
3. Run import commands:

```bash
# Download CSVs from S3
python3 -c "
from app.services.s3_downloader import CourtListenerDownloader
downloader = CourtListenerDownloader()

files = [
    'bulk-data/search_docket-2025-10-31.csv.bz2',
    'bulk-data/search_opinionscited-2025-10-31.csv.bz2',
    'bulk-data/opinion-clusters-2025-10-31.csv.bz2',
]

for file in files:
    print(f'Downloading {file}...')
    downloader.download_file(file)
"

# Run imports
python3 -c "
from pathlib import Path
from app.services.data_importer import DataImporter
from app.core.database import SessionLocal

importer = DataImporter(data_dir=Path('/app/data'))
session = SessionLocal()

tables = [
    ('search_docket', 'search_docket-2025-10-31.csv', 'import_csv'),
    ('search_opinionscited', 'search_opinionscited-2025-10-31.csv', 'import_csv'),
    ('search_opinioncluster', 'search_opinioncluster-2025-10-31.csv', 'import_csv_pandas'),
]

for table_name, csv_file, method in tables:
    csv_path = Path(f'/app/data/{csv_file}')
    if method == 'import_csv_pandas':
        importer.import_csv_pandas(table_name, csv_path, session)
    else:
        importer.import_csv(table_name, csv_path, session)
"
```

**Expected time**: 6-8 hours (can run overnight)

---

### 📋 Testing

#### Backend Health Check
```bash
curl https://your-railway-url.railway.app/health
```

#### Frontend Load Test
Open: `https://your-vercel-url.vercel.app`

#### API Integration Test
1. Open frontend in browser
2. Try searching for a docket
3. Check if data loads from Railway backend

---

## Credentials Reference

### Railway Database
- **Internal URL**: `postgresql://postgres:***@postgres.railway.internal:5432/railway`
- **Public URL**: `postgresql://postgres:***@crossover.proxy.rlwy.net:56007/railway`

### GitHub Repository
- **URL**: https://github.com/alexmclaughlin2005/caselaw

---

## Troubleshooting

### Backend won't deploy
- Check Railway logs: Service → Deployments → Click latest → View logs
- Common issues:
  - Missing DATABASE_URL (add reference to PostgreSQL)
  - Dockerfile path incorrect (should be `backend/Dockerfile`)
  - Requirements not installed (check logs)

### Frontend won't connect to backend
- Verify VITE_API_URL in Vercel environment variables
- Check CORS: Railway backend ALLOWED_ORIGINS includes Vercel URL
- Test backend directly: `curl https://railway-url/health`

### Database connection fails
- Verify DATABASE_URL is set in Railway variables
- Check PostgreSQL service is running
- Try redeploying backend after linking database

---

## Next Steps After Deployment

1. Monitor Railway logs during data import
2. Set up Railway usage alerts (prevent unexpected costs)
3. Configure custom domain (optional)
4. Set up monitoring/analytics
5. Create backup schedule for database

---

**Last Updated**: 2025-11-13
**Status**: Railway setup in progress
