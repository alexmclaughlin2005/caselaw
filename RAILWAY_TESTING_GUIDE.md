# Testing CSV Chunking on Railway

## Step 1: Run the Migration

Since your database is on Railway, we've created an API endpoint to run the migration from within your deployed service.

### Option A: Using curl (Recommended)

```bash
# Check if table exists
curl https://your-railway-app.up.railway.app/api/migration/check-chunk-table

# If it doesn't exist, create it
curl -X POST https://your-railway-app.up.railway.app/api/migration/run-chunk-table-migration

# Verify it was created
curl https://your-railway-app.up.railway.app/api/migration/check-chunk-table
```

### Option B: Using the API docs

1. Open your Railway app URL: `https://your-railway-app.up.railway.app/docs`
2. Find the `/api/migration/run-chunk-table-migration` endpoint
3. Click "Try it out" and "Execute"
4. Check the response to confirm the table was created

## Step 2: Get Your Railway App URL

```bash
railway status
```

This will show your deployment URL.

## Step 3: Test the Chunking System

Once the migration is complete, you can test the chunking endpoints:

### Check Chunks Status
```bash
curl https://your-railway-app.up.railway.app/api/chunks/search_docket/2025-10-31
```

### Create Chunks (if you have a CSV uploaded)
```bash
curl -X POST https://your-railway-app.up.railway.app/api/chunks/chunk \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "search_docket",
    "dataset_date": "2025-10-31",
    "csv_filename": "search_docket-2025-10-31.csv",
    "chunk_size": 1000000
  }'
```

### Check Progress
```bash
curl https://your-railway-app.up.railway.app/api/chunks/search_docket/2025-10-31/progress
```

## Step 4: Test Locally Against Railway Database

If you want to run the chunking CLI tool locally against your Railway database:

1. Get your DATABASE_URL:
```bash
railway variables | grep DATABASE_URL
```

2. Set it locally:
```bash
export DATABASE_URL="your-database-url-from-above"
```

3. Run the CLI:
```bash
python chunk_and_import.py progress --table search_docket --date 2025-10-31
```

## Current Status

Your CSV chunking system is now fully implemented:

✅ Database model created
✅ Service layer implemented
✅ API endpoints added
✅ CLI tool ready
✅ Migration endpoint created
⏳ Waiting for migration to run on Railway

## Next Steps

1. **Run the migration** using the API endpoint (see Step 1 above)
2. **Upload a CSV** to your Railway service (or use existing CSVs)
3. **Create chunks** using the API or CLI
4. **Import chunks** sequentially with progress tracking

## Troubleshooting

### Can't access Railway app

Check that your service is deployed and running:
```bash
railway status
railway logs
```

### Table already exists

If you get "table already exists", that's fine! The chunking system is ready to use.

### Need to re-run migration

The endpoint is safe to call multiple times - it uses `IF NOT EXISTS`.

## Documentation

- **Complete Guide**: [CSV_CHUNKING_GUIDE.md](CSV_CHUNKING_GUIDE.md)
- **Quick Reference**: [CHUNKING_QUICK_REFERENCE.md](CHUNKING_QUICK_REFERENCE.md)
- **API Docs**: `https://your-railway-app.up.railway.app/docs`
