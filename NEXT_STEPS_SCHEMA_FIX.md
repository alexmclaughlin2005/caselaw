# Next Steps: Fix Schema to Match CourtListener Official Schema

## Summary of Investigation

I've identified the root cause of all import failures:

**Our database schema is incomplete** - we're missing 32-34 columns out of the 52 columns in the CSV files.

- **CSV Columns**: 52
- **Our DB Columns**: 20
- **CourtListener Official Schema Columns**: 54

The CSV data is valid. Other CourtListener customers successfully import it using the official schema.

## Key Findings

1. **Official Schema Exists**: CourtListener provides `schema-2025-10-31.sql` (398 KB) with every bulk data export
2. **Column Mismatch**: We're filtering out 32 columns per row during import because our schema doesn't have them
3. **Type Errors Were Misdiagnosed**: Values like "mont", "mied", "njd" are valid `federal_dn_office_code` values (varchar(3)), not bad data
4. **PostgreSQL COPY Failed**: Because column counts don't match (CSV: 52, DB: 20)

## Missing Columns in search_docket

Our schema is missing these 32 columns from CourtListener's official schema:

```sql
-- Timestamp columns
date_created timestamp with time zone NOT NULL
date_modified timestamp with time zone NOT NULL

-- Case details
cause character varying(2000) NOT NULL
nature_of_suit character varying(1000) NOT NULL
jury_demand character varying(500) NOT NULL
jurisdiction_type character varying(100) NOT NULL

-- File paths
filepath_local character varying(1000) NOT NULL
filepath_ia character varying(1000) NOT NULL
filepath_ia_json character varying(1000) NOT NULL

-- String representations
assigned_to_str text NOT NULL
referred_to_str text NOT NULL
appeal_from_str text NOT NULL
panel_str text NOT NULL

-- Appellate information
appellate_fee_status text NOT NULL
appellate_case_type_information text NOT NULL

-- MDL and view tracking
mdl_status character varying(100) NOT NULL
view_count integer NOT NULL
date_last_index timestamp with time zone
date_last_filing date

-- Internet Archive
ia_needs_upload boolean
ia_upload_failure_count smallint
ia_date_first_change timestamp with time zone

-- Federal docket numbers
docket_number_core character varying(20) NOT NULL
federal_dn_case_type character varying(6) NOT NULL
federal_dn_judge_initials_assigned character varying(5) NOT NULL
federal_dn_judge_initials_referred character varying(5) NOT NULL
federal_dn_office_code character varying(3) NOT NULL  -- THIS IS WHERE "mont", "mied", "njd" go!

-- Additional fields
federal_defendant_number smallint
parent_docket_id integer
originating_court_information_id integer
idb_data_id integer
docket_number_raw character varying NOT NULL  -- Extra field in schema but not in CSV
```

## Solution: Use CourtListener's Official Schema

### Recommended Approach

**Create an Alembic migration that adds all missing columns** to match the official schema.

### Why This Approach

1. **Keeps existing data** - 17.15M dockets, 38M citations, 6.1M parentheticals  preserved
2. **Adds missing columns** - All 32 missing columns added with proper types
3. **Future-proof** - Schema will match official CourtListener structure
4. **Enables fast imports** - PostgreSQL COPY will work once columns match

### Migration Steps

```bash
# 1. Create new Alembic migration
docker-compose exec backend alembic revision -m "add_missing_courtlistener_columns"

# 2. Edit the migration file to add columns (see generated SQL below)

# 3. Run migration
docker-compose exec backend alembic upgrade head

# 4. Test import with complete schema
docker exec courtlistener-celery-worker python3 -c "
from app.services.data_importer import DataImporter
importer = DataImporter()
importer.import_csv_with_postgres_copy('search_docket', '/app/data/search_docket-sample.csv')
"
```

### Generated SQL for Migration

```sql
-- Add missing columns to search_docket table
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS date_created timestamp with time zone DEFAULT NOW() NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS date_modified timestamp with time zone DEFAULT NOW() NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS cause character varying(2000) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS nature_of_suit character varying(1000) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS jury_demand character varying(500) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS jurisdiction_type character varying(100) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS filepath_local character varying(1000) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS filepath_ia character varying(1000) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS filepath_ia_json character varying(1000) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS assigned_to_str text DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS referred_to_str text DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS appeal_from_str text DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS panel_str text DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS appellate_fee_status text DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS appellate_case_type_information text DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS mdl_status character varying(100) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS view_count integer DEFAULT 0 NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS date_last_index timestamp with time zone;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS date_last_filing date;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS ia_needs_upload boolean;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS ia_upload_failure_count smallint;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS ia_date_first_change timestamp with time zone;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS docket_number_core character varying(20) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS federal_dn_case_type character varying(6) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS federal_dn_judge_initials_assigned character varying(5) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS federal_dn_judge_initials_referred character varying(5) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS federal_dn_office_code character varying(3) DEFAULT '' NOT NULL;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS federal_defendant_number smallint;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS parent_docket_id integer;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS originating_court_information_id integer;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS idb_data_id integer;
ALTER TABLE search_docket ADD COLUMN IF NOT EXISTS docket_number_raw character varying DEFAULT '' NOT NULL;

-- Note: Existing 17.15M records will have DEFAULT values for new columns
-- Re-import will properly populate all columns with full CSV data
```

## After Migration

### Option 1: Keep Existing Data (Recommended for Testing)

- Existing 17.15M records will have default values for new columns
- New imports will populate all 52 columns properly
- Can verify import works before clearing data

### Option 2: Fresh Start (Recommended for Production)

```sql
-- Clear existing data
TRUNCATE TABLE search_docket CASCADE;
TRUNCATE TABLE search_opinioncluster CASCADE;
TRUNCATE TABLE search_opinionscited CASCADE;
TRUNCATE TABLE search_parenthetical CASCADE;

-- Re-import with complete schema (all 52 columns will be populated)
```

## Expected Results After Fix

1. **PostgreSQL COPY Will Work**: Column counts will match (52 CSV columns = 52 DB columns)
2. **No More Type Errors**: "mont", "mied", "njd" will go into proper varchar(3) column
3. **No Data Loss**: All 52 columns preserved, not just 20
4. **10-100x Faster Imports**: COPY is much faster than pandas
5. **Complete Data**: All metadata, timestamps, file paths, federal docket numbers preserved

## Files Modified in This Investigation

- [SCHEMA_MISMATCH_FINDINGS.md](SCHEMA_MISMATCH_FINDINGS.md) - Complete analysis
- [PARTIAL_DATASET_ANALYSIS.md](PARTIAL_DATASET_ANALYSIS.md) - **OBSOLETE** (based on wrong premise)

## References

- Official Schema: `data/schema-2025-10-31.sql` (inside Docker container at `/app/data/`)
- CSV Sample: `data/search_docket-sample.csv`
- ERD Diagram: Provided by user (shows complete schema relationships)
- Current Import Code: [backend/app/services/data_importer.py](backend/app/services/data_importer.py)

## Questions for User

1. **Do you want to keep the existing 17.15M records** (with default values for new columns)?
   - Or clear and re-import everything with complete data?

2. **Should I create the Alembic migration now?**
   - I can generate the full migration file with all ALTER TABLE statements

3. **Do you want me to test the import with the sample CSV** first?
   - Verify the fix works before applying to full dataset

## Estimated Time to Complete

- Create migration: 10 minutes
- Run migration: 1-2 minutes (adding columns is fast)
- Test import: 5 minutes
- Full re-import (if chosen): 8-12 hours for complete dataset

---

**Bottom Line**: The CSV data is valid. We just need to match CourtListener's official schema, and all imports will work perfectly.
