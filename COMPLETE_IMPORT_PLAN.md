# Complete Data Import Plan - Court Listener Database

## Executive Summary

**Current Status**:
- ✅ **search_opinioncluster**: Importing with correct schema (8M / 74.6M records)
- ⚠️ **search_docket**: Incomplete import (47.2M / 70M - missing 32.6%)
- ⚠️ **search_opinionscited**: Incomplete import (48.4M / 75.8M - missing 36.2%)

**Objective**: Complete all three table imports with full data and correct schemas

---

## Phase 1: Monitor Current Import (3-4 hours)

### Task 1.1: Monitor search_opinioncluster to Completion
**Status**: IN PROGRESS
**Current**: 8M / 74.6M records (10.7%)
**ETA**: ~3-4 hours
**Rate**: ~5,500 rows/second

**Actions**:
- Check status every 30-60 minutes
- Verify column population continues correctly
- Watch for errors in logs

**Success Criteria**:
- All ~74.6M records imported
- All 36 CSV columns populated
- No critical errors

---

## Phase 2: Verify and Document (15 mins)

### Task 2.1: Verify search_opinioncluster Completion
**Actions**:
```bash
# Check final count
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener \
  -c "SELECT COUNT(*) FROM search_opinioncluster;"

# Verify column population
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener -c "
SELECT
    COUNT(*) as total,
    COUNT(headmatter) as has_headmatter,
    COUNT(disposition) as has_disposition,
    COUNT(filepath_json_harvard) as has_harvard_json,
    ROUND(100.0 * COUNT(headmatter) / COUNT(*), 1) as pct_headmatter
FROM search_opinioncluster;
"

# Check for skipped rows in logs
docker logs courtlistener-celery-worker 2>&1 | grep -i "skipped"
```

**Success Criteria**:
- Final count: 60-70M records (80-95% of CSV)
- headmatter, disposition, harvard paths populated
- Documented skipped row count

---

## Phase 3: Check Other Table Schemas (10 mins)

### Task 3.1: Verify search_docket Schema
**Concern**: May have same missing column issue

**Actions**:
```bash
# Check database schema
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener \
  -c "\d search_docket"

# Get CSV columns
docker exec courtlistener-celery-worker head -1 /app/data/search_docket-2025-10-31.csv

# Compare column counts
docker exec courtlistener-celery-worker python3 -c "
import csv
from sqlalchemy import inspect
from app.core.database import engine

# Get CSV columns
with open('/app/data/search_docket-2025-10-31.csv', 'r') as f:
    reader = csv.reader(f)
    csv_cols = next(reader)

# Get DB columns
inspector = inspect(engine)
db_cols = [c['name'] for c in inspector.get_columns('search_docket')]

print(f'CSV columns: {len(csv_cols)}')
print(f'DB columns: {len(db_cols)}')

missing = set(csv_cols) - set(db_cols)
if missing:
    print(f'Missing in DB: {missing}')
else:
    print('✓ All CSV columns exist in DB')
"
```

### Task 3.2: Verify search_opinionscited Schema
Same checks as above for search_opinionscited table.

**Expected Outcome**: Identify any missing columns that need migrations

---

## Phase 4: Fix Schemas if Needed (30 mins)

### Task 4.1: Create Migrations (if needed)
**Only if Phase 3 found missing columns**

**Actions**:
1. Create migration for missing columns
2. Apply migration with `alembic upgrade head`
3. Update SQLAlchemy models
4. Verify schema matches CSV

### Task 4.2: Update Models
Update SQLAlchemy models to match database schemas

---

## Phase 5: Import search_docket (3-4 hours)

### Task 5.1: Truncate Incomplete Data
**Current**: 47.2M incomplete records
**Action**: Remove and start fresh

```bash
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener \
  -c "TRUNCATE search_docket CASCADE;"
```

### Task 5.2: Start Import
**Expected Records**: ~70M
**Expected Time**: 3-4 hours at 5,500 rows/sec
**CSV**: search_docket-2025-10-31.csv (26 GB)

```bash
docker exec courtlistener-celery-worker nohup python3 -c "
from pathlib import Path
from app.services.data_importer import DataImporter
from app.core.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info('Starting search_docket import...')
importer = DataImporter(data_dir=Path('/app/data'))
session = SessionLocal()

try:
    csv_path = Path('/app/data/search_docket-2025-10-31.csv')
    row_count = importer.import_csv('search_docket', csv_path, session)
    logger.info(f'Import completed: {row_count:,} rows')
except Exception as e:
    logger.error(f'Import failed: {e}')
    import traceback
    traceback.print_exc()
finally:
    session.close()
" > /tmp/docket_import.log 2>&1 &
```

### Task 5.3: Monitor Progress
Check every 30-60 minutes:

```bash
# Check count
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener \
  -c "SELECT COUNT(*) FROM search_docket;"

# Check worker
docker stats courtlistener-celery-worker --no-stream
```

**Success Criteria**:
- 60-65M records imported (85-95% of 70M)
- No schema mismatch warnings
- Stable progress with no stalls

---

## Phase 6: Import search_opinionscited (3-4 hours)

### Task 6.1: Truncate Incomplete Data
**Current**: 48.4M incomplete records
**Action**: Remove and start fresh

```bash
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener \
  -c "TRUNCATE search_opinionscited CASCADE;"
```

### Task 6.2: Start Import
**Expected Records**: ~75.8M
**Expected Time**: 3-4 hours at 5,500 rows/sec
**CSV**: search_opinionscited-2025-10-31.csv (2.6 GB)

```bash
docker exec courtlistener-celery-worker nohup python3 -c "
from pathlib import Path
from app.services.data_importer import DataImporter
from app.core.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info('Starting search_opinionscited import...')
importer = DataImporter(data_dir=Path('/app/data'))
session = SessionLocal()

try:
    csv_path = Path('/app/data/search_opinionscited-2025-10-31.csv')
    row_count = importer.import_csv('search_opinionscited', csv_path, session)
    logger.info(f'Import completed: {row_count:,} rows')
except Exception as e:
    logger.error(f'Import failed: {e}')
    import traceback
    traceback.print_exc()
finally:
    session.close()
" > /tmp/opinionscited_import.log 2>&1 &
```

### Task 6.3: Monitor Progress
Same monitoring as search_docket

**Success Criteria**:
- 65-70M records imported (85-95% of 75.8M)
- No schema mismatch warnings
- Stable progress with no stalls

---

## Phase 7: Final Verification (30 mins)

### Task 7.1: Verify All Table Counts

```bash
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener -c "
SELECT 'search_opinioncluster' as table_name, COUNT(*) as records FROM search_opinioncluster
UNION ALL
SELECT 'search_docket', COUNT(*) FROM search_docket
UNION ALL
SELECT 'search_opinionscited', COUNT(*) FROM search_opinionscited
UNION ALL
SELECT 'search_parenthetical', COUNT(*) FROM search_parenthetical
ORDER BY table_name;
"
```

**Expected Results**:
| Table | Expected | Acceptable Range |
|-------|----------|------------------|
| search_opinioncluster | 74.6M | 60-70M (80-95%) |
| search_docket | 70M | 60-65M (85-95%) |
| search_opinionscited | 75.8M | 65-70M (85-95%) |
| search_parenthetical | 6.1M | 5-6M (85-95%) |

### Task 7.2: Verify Data Quality

```bash
# Check for NULL in critical fields
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener -c "
SELECT
    COUNT(*) as total,
    COUNT(case_name) as has_case_name,
    COUNT(docket_id) as has_docket_id,
    ROUND(100.0 * COUNT(case_name) / COUNT(*), 1) as pct_case_name
FROM search_opinioncluster;
"

# Check docket data
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener -c "
SELECT
    COUNT(*) as total,
    COUNT(case_name) as has_case_name,
    COUNT(court_id) as has_court_id,
    ROUND(100.0 * COUNT(case_name) / COUNT(*), 1) as pct_case_name
FROM search_docket;
"
```

### Task 7.3: Check Import Logs for Errors

```bash
# Check for errors in logs
docker logs courtlistener-celery-worker 2>&1 | grep -i "error\|failed\|skipped" | tail -50
```

### Task 7.4: Verify Database Size

```bash
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener -c "
SELECT
    pg_size_pretty(pg_database_size('courtlistener')) as db_size;
"
```

**Expected**: 40-60 GB total database size

---

## Phase 8: Documentation (30 mins)

### Task 8.1: Update IMPORT_STATUS.md

Document:
- Final record counts for all tables
- Import success rates (% of CSV imported)
- Total skipped rows per table
- Schema fixes applied
- Total import time
- Any remaining issues

### Task 8.2: Create Final Summary Report

Include:
- ✅ Completed tables with record counts
- ⚠️ Any issues encountered
- 📊 Import statistics
- 🔍 Data quality metrics
- 📝 Lessons learned
- 🚀 Next steps (if any)

---

## Timeline Summary

| Phase | Task | Duration | Cumulative |
|-------|------|----------|------------|
| 1 | Monitor opinioncluster import | 3-4 hours | 3-4 hours |
| 2 | Verify completion | 15 mins | 3.25-4.25 hours |
| 3 | Check other schemas | 10 mins | 3.5-4.5 hours |
| 4 | Fix schemas (if needed) | 30 mins | 4-5 hours |
| 5 | Import search_docket | 3-4 hours | 7-9 hours |
| 6 | Import search_opinionscited | 3-4 hours | 10-13 hours |
| 7 | Final verification | 30 mins | 10.5-13.5 hours |
| 8 | Documentation | 30 mins | 11-14 hours |

**Total Estimated Time**: 11-14 hours (can run overnight)

---

## Risk Mitigation

### Risk 1: Schema Mismatches
**Mitigation**: Phase 3 checks all schemas before importing
**Fallback**: Create migrations immediately if issues found

### Risk 2: Import Stalls/Crashes
**Mitigation**: Monitor every 30-60 minutes
**Fallback**: Restart import from last commit point (ON CONFLICT DO NOTHING allows resume)

### Risk 3: Disk Space
**Mitigation**: Monitor disk usage during imports
**Fallback**: Clean up old CSVs if needed

### Risk 4: Memory Issues
**Mitigation**: Current chunk size (100K) keeps memory stable at ~600MB
**Fallback**: Reduce chunk size if memory spikes

---

## Success Criteria

**Must Have**:
- ✅ All 4 tables have data
- ✅ 80%+ of CSV records imported for each table
- ✅ No schema mismatch errors
- ✅ All critical columns populated

**Nice to Have**:
- 90%+ import success rate
- < 5% skipped rows per table
- Complete data quality documentation
- Performance metrics for future imports

---

## Monitoring Commands (Quick Reference)

```bash
# Check all table counts
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener -c "
SELECT 'opinioncluster' as t, COUNT(*) as count FROM search_opinioncluster
UNION ALL SELECT 'docket', COUNT(*) FROM search_docket
UNION ALL SELECT 'opinionscited', COUNT(*) FROM search_opinionscited
UNION ALL SELECT 'parenthetical', COUNT(*) FROM search_parenthetical;"

# Check worker status
docker stats courtlistener-celery-worker --no-stream

# Check recent logs
docker logs courtlistener-celery-worker 2>&1 | tail -50

# Check database size
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener -c "
SELECT pg_size_pretty(pg_database_size('courtlistener'));"
```

---

**Last Updated**: 2025-11-12 21:00 UTC
**Status**: Phase 1 in progress (opinioncluster at 8M records)
**Next Action**: Monitor opinioncluster import to completion
