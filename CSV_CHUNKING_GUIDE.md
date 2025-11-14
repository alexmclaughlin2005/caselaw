# CSV Chunking System Guide

## Overview

The CSV Chunking System provides a safe, incremental method for importing massive CSV files into PostgreSQL. Instead of processing entire multi-gigabyte files at once, this system splits them into manageable chunks and tracks progress per chunk, enabling:

- **Resumable imports**: Restart from last successful chunk after failures
- **Progress tracking**: Monitor import status chunk-by-chunk
- **Error isolation**: Failed chunks don't affect successful ones
- **Memory efficiency**: Process large files without loading entirely into memory
- **Sequential safety**: Import chunks one at a time for stability

## Architecture

### Components

1. **Database Model** ([csv_chunk_progress.py](backend/app/models/csv_chunk_progress.py))
   - Tracks progress per chunk
   - Stores timing, row counts, errors
   - Enables resumable imports

2. **Service Layer** ([csv_chunk_manager.py](backend/app/services/csv_chunk_manager.py))
   - Core chunking logic
   - Sequential import with progress tracking
   - Error handling and retry logic

3. **API Endpoints** ([chunk_management.py](backend/app/api/routes/chunk_management.py))
   - RESTful API for chunk operations
   - Progress monitoring endpoints
   - Management operations (reset, delete)

4. **CLI Script** ([chunk_and_import.py](chunk_and_import.py))
   - Standalone command-line tool
   - No server required
   - Direct database access

## Installation

### Database Migration

Run the migration to create the `csv_chunk_progress` table:

```bash
# Using Docker
docker compose exec backend alembic upgrade head

# Or directly
cd backend
alembic upgrade head
```

### Dependencies

All required dependencies are already included in `requirements.txt`:
- `sqlalchemy` - ORM and database operations
- `fastapi` - API framework
- `pandas` (optional) - For pandas import method

## Usage

### Method 1: CLI Script (Recommended)

The CLI script provides the simplest way to chunk and import CSV files.

#### 1. Chunk a CSV File

```bash
# Chunk a large CSV into 1M row chunks
python chunk_and_import.py chunk \
  --table search_docket \
  --date 2025-10-31 \
  --chunk-size 1000000
```

This creates:
- Chunk files: `data/chunks/search_docket-2025-10-31/search_docket-2025-10-31.chunk_0001.csv`
- Database records: One per chunk in `csv_chunk_progress` table

#### 2. Import Chunks Sequentially

```bash
# Import all chunks with standard method
python chunk_and_import.py import \
  --table search_docket \
  --date 2025-10-31 \
  --method standard

# Resume mode (skip completed chunks)
python chunk_and_import.py import \
  --table search_docket \
  --date 2025-10-31 \
  --method standard \
  --max-retries 3

# Force re-import (no resume)
python chunk_and_import.py import \
  --table search_docket \
  --date 2025-10-31 \
  --method pandas \
  --no-resume
```

**Import Methods:**
- `standard` - Native Python CSV parsing (500K chunks, fast)
- `pandas` - Robust pandas parser (handles malformed CSVs)
- `copy` - PostgreSQL COPY command (fastest, requires clean data)

#### 3. Check Progress

```bash
# Quick summary
python chunk_and_import.py progress \
  --table search_docket \
  --date 2025-10-31

# Detailed chunk-by-chunk status
python chunk_and_import.py progress \
  --table search_docket \
  --date 2025-10-31 \
  --detailed
```

Output:
```
================================================================================
IMPORT PROGRESS
================================================================================
Table: search_docket
Date: 2025-10-31
Status: in_progress

Chunks:
  Total: 35
  Completed: 18
  Failed: 1
  Processing: 0
  Pending: 16

Rows:
  Total: 34,900,000
  Imported: 18,000,000
  Skipped: 1,234

Progress: 51.4%
```

#### 4. Reset Chunks (for re-import)

```bash
# Reset all chunks to pending
python chunk_and_import.py reset \
  --table search_docket \
  --date 2025-10-31
```

#### 5. Delete Chunks

```bash
# Delete database records only (keep files)
python chunk_and_import.py delete \
  --table search_docket \
  --date 2025-10-31

# Delete both records and files
python chunk_and_import.py delete \
  --table search_docket \
  --date 2025-10-31 \
  --delete-files \
  --yes
```

### Method 2: API Endpoints

Use the REST API for programmatic access or integration with the frontend.

#### Chunk a CSV

```bash
POST /api/chunks/chunk
Content-Type: application/json

{
  "table_name": "search_docket",
  "dataset_date": "2025-10-31",
  "csv_filename": "search_docket-2025-10-31.csv",
  "chunk_size": 1000000
}
```

#### List Chunks

```bash
GET /api/chunks/search_docket/2025-10-31
```

Response:
```json
{
  "table_name": "search_docket",
  "dataset_date": "2025-10-31",
  "total_chunks": 35,
  "chunks": [
    {
      "chunk_number": 1,
      "chunk_filename": "search_docket-2025-10-31.chunk_0001.csv",
      "status": "completed",
      "chunk_row_count": 1000000,
      "rows_imported": 999876,
      "duration_seconds": 145
    },
    ...
  ]
}
```

#### Get Progress Summary

```bash
GET /api/chunks/search_docket/2025-10-31/progress
```

#### Import Chunks

```bash
POST /api/chunks/import
Content-Type: application/json

{
  "table_name": "search_docket",
  "dataset_date": "2025-10-31",
  "import_method": "standard",
  "resume": true,
  "max_retries": 3
}
```

### Method 3: Python API

Use directly in Python code:

```python
from pathlib import Path
from app.services.csv_chunk_manager import CSVChunkManager
from app.core.database import SessionLocal

# Initialize
session = SessionLocal()
manager = CSVChunkManager()

# Chunk a CSV
csv_path = Path("/app/data/search_docket-2025-10-31.csv")
chunks = manager.chunk_csv(
    csv_path=csv_path,
    table_name="search_docket",
    dataset_date="2025-10-31",
    chunk_size=1_000_000,
    db_session=session
)

# Import chunks
results = manager.import_chunked(
    table_name="search_docket",
    dataset_date="2025-10-31",
    import_method="standard",
    resume=True,
    max_retries=3,
    db_session=session
)

print(f"Imported {results['total_rows_imported']:,} rows")
print(f"Success: {results['successful_chunks']}/{results['total_chunks']} chunks")

session.close()
```

## Configuration

### Chunk Size Selection

Choose chunk size based on table characteristics:

| Table | Avg Row Size | Recommended Chunk Size | Rationale |
|-------|--------------|----------------------|-----------|
| `search_docket` | Small (~500 bytes) | 1,000,000 rows | Fast processing, frequent commits |
| `search_opinioncluster` | Medium (~2KB) | 500,000 rows | Balance between speed and memory |
| `search_opinionscited` | Small (~200 bytes) | 2,000,000 rows | Lightweight, can process more |
| `search_parenthetical` | Large (~5KB HTML) | 250,000 rows | Large text fields need smaller chunks |

### Import Method Selection

| Method | Speed | Robustness | Use Case |
|--------|-------|------------|----------|
| `standard` | Fast (50-100K rows/min) | Good | Clean CSV data, default choice |
| `pandas` | Medium (30-80K rows/min) | Excellent | Malformed CSVs, encoding issues |
| `copy` | Very Fast (200-500K rows/min) | Limited | Perfect CSV format only |

## Error Handling

### Automatic Retry Logic

The import system includes automatic retry for failed chunks:

```python
# Each chunk is retried up to max_retries times (default: 3)
# Exponential backoff between retries
# Failed chunks are marked with error messages
```

### Resume After Failure

If an import fails mid-way:

1. **Check progress** to see which chunks failed:
   ```bash
   python chunk_and_import.py progress --table search_docket --date 2025-10-31 --detailed
   ```

2. **Resume import** (skips completed chunks):
   ```bash
   python chunk_and_import.py import --table search_docket --date 2025-10-31
   ```

3. **Reset failed chunks** if needed:
   ```bash
   # Reset only failed chunks by deleting their records
   # Then re-run import with resume=true
   ```

### Common Issues

#### "No chunks found"
**Cause**: Chunks not created yet
**Solution**: Run `chunk` command first before `import`

#### "Chunk file not found"
**Cause**: Chunk files deleted manually
**Solution**: Delete chunk records and re-chunk the original CSV

#### "Data type mismatch" (COPY method)
**Cause**: CSV has invalid data for PostgreSQL COPY
**Solution**: Use `standard` or `pandas` method instead

## Performance

### Expected Import Rates

Based on testing with CourtListener data:

| Method | Rows/Min | 35M Rows (Dockets) | 7M Rows (Opinions) |
|--------|----------|-------------------|-------------------|
| Standard | 50-100K | 5.8-11.6 hours | 1.2-2.3 hours |
| Pandas | 30-80K | 7.3-19.4 hours | 1.5-3.9 hours |
| COPY | 200-500K | 1.2-2.9 hours | 14-35 minutes |

### Optimization Tips

1. **Disable foreign key checks** for bulk imports:
   ```sql
   SET session_replication_role = 'replica';  -- Disable FK checks
   -- Run import
   SET session_replication_role = 'origin';   -- Re-enable FK checks
   ```

2. **Increase chunk size** for small tables (faster commits, less overhead)

3. **Use COPY method** if your CSV is clean and well-formatted

4. **Run during off-peak hours** to avoid resource contention

5. **Monitor disk space** - chunks directory can grow large

## Database Schema

The `csv_chunk_progress` table stores:

```sql
CREATE TABLE csv_chunk_progress (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    dataset_date VARCHAR(20) NOT NULL,
    chunk_number INTEGER NOT NULL,
    chunk_filename VARCHAR(255) NOT NULL,
    chunk_start_row BIGINT,
    chunk_end_row BIGINT,
    chunk_row_count BIGINT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    rows_imported BIGINT DEFAULT 0,
    rows_skipped BIGINT DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    import_method VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Status Values:**
- `pending` - Chunk created, not yet processed
- `processing` - Currently being imported
- `completed` - Successfully imported
- `failed` - Import failed after retries
- `skipped` - Skipped due to resume mode

## API Reference

### POST /api/chunks/chunk
Create chunks from a CSV file.

**Request Body:**
```json
{
  "table_name": "string",
  "dataset_date": "string",
  "csv_filename": "string",
  "chunk_size": 1000000
}
```

**Response:** `ChunkListResponse` with created chunks

---

### GET /api/chunks/{table_name}/{dataset_date}
List all chunks for a table/date.

**Response:** `ChunkListResponse` with chunk details

---

### GET /api/chunks/{table_name}/{dataset_date}/progress
Get progress summary for chunked import.

**Response:** `ChunkProgressSummary` with statistics

---

### POST /api/chunks/import
Import all chunks sequentially.

**Request Body:**
```json
{
  "table_name": "string",
  "dataset_date": "string",
  "import_method": "standard",
  "resume": true,
  "max_retries": 3
}
```

**Response:** `ChunkedImportResponse` with results

---

### POST /api/chunks/reset
Reset chunks to pending status.

**Request Body:**
```json
{
  "table_name": "string",
  "dataset_date": "string"
}
```

---

### DELETE /api/chunks
Delete chunk records and optionally files.

**Request Body:**
```json
{
  "table_name": "string",
  "dataset_date": "string",
  "delete_files": true
}
```

## Best Practices

1. **Always chunk before import** - Don't skip the chunking step
2. **Use resume mode** - Saves time on re-imports
3. **Monitor progress** - Check regularly during long imports
4. **Keep original CSVs** - In case you need to re-chunk
5. **Test with small chunks** - Verify your import logic first
6. **Clean up old chunks** - Delete completed chunks to save disk space
7. **Document your settings** - Record chunk size and method used

## Troubleshooting

### Slow Import Speed

1. Check database connection pool size
2. Increase chunk size to reduce commit overhead
3. Disable foreign key checks temporarily
4. Verify disk I/O isn't bottlenecked
5. Try different import methods

### Memory Issues

1. Reduce chunk size
2. Use `standard` method instead of `pandas`
3. Check available RAM on server
4. Close other applications

### Chunk Files Too Large

1. Reduce chunk size (e.g., from 1M to 500K rows)
2. Delete old chunks after successful import
3. Monitor `data/chunks/` directory size

## Examples

### Example 1: Import Large Docket Table

```bash
# Step 1: Chunk the 35M row docket CSV (this is fast, ~5 minutes)
python chunk_and_import.py chunk \
  --table search_docket \
  --date 2025-10-31 \
  --chunk-size 1000000

# Step 2: Import chunks sequentially (~10 hours with standard method)
python chunk_and_import.py import \
  --table search_docket \
  --date 2025-10-31 \
  --method standard

# Step 3: Monitor progress in another terminal
watch -n 30 'python chunk_and_import.py progress --table search_docket --date 2025-10-31'
```

### Example 2: Resume Failed Import

```bash
# Check what failed
python chunk_and_import.py progress \
  --table search_docket \
  --date 2025-10-31 \
  --detailed

# Resume (skips completed chunks automatically)
python chunk_and_import.py import \
  --table search_docket \
  --date 2025-10-31 \
  --method standard
```

### Example 3: Clean CSV with COPY Method

```bash
# Use ultra-fast COPY method for clean data
python chunk_and_import.py import \
  --table search_opinionscited \
  --date 2025-10-31 \
  --method copy
```

## Support

For issues or questions:
1. Check logs in `backend/logs/` directory
2. Review error messages in chunk progress table
3. Consult [AI_instructions.md](AI_instructions.md) for architecture details
4. Check GitHub issues at the repository

## Future Enhancements

Potential improvements for future versions:
- [ ] Parallel chunk imports (careful with FK constraints)
- [ ] Automatic chunk size optimization based on row size
- [ ] Web UI for progress monitoring
- [ ] Email notifications on completion/failure
- [ ] Automatic cleanup of old chunks
- [ ] Compression of chunk files
- [ ] S3 integration for chunk storage
