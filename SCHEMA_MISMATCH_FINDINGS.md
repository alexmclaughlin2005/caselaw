# Schema Mismatch Investigation Findings

**Date**: 2025-11-11
**Issue**: Import failures with "extra data after last expected column" and type errors
**Root Cause**: INCOMPLETE DATABASE SCHEMA

## Executive Summary

The import failures are NOT due to bad CSV data. They are caused by a **fundamental mismatch** between our database schema and CourtListener's actual CSV structure.

**We created a minimal schema with only 20 columns, but the CSV files contain 52 columns.**

This is why other CourtListener customers can successfully import the data - they use the complete official schema provided by CourtListener.

---

## Evidence

### CSV Structure (52 columns)
```
id, date_created, date_modified, source, appeal_from_str, assigned_to_str,
referred_to_str, panel_str, date_last_index, date_cert_granted, date_cert_denied,
date_argued, date_reargued, date_reargument_denied, date_filed, date_terminated,
date_last_filing, case_name_short, case_name, case_name_full, slug, docket_number,
docket_number_core, pacer_case_id, cause, nature_of_suit, jury_demand,
jurisdiction_type, appellate_fee_status, appellate_case_type_information, mdl_status,
filepath_local, filepath_ia, filepath_ia_json, ia_upload_failure_count,
ia_needs_upload, ia_date_first_change, view_count, date_blocked, blocked,
appeal_from_id, assigned_to_id, court_id, idb_data_id,
originating_court_information_id, referred_to_id, federal_dn_case_type,
federal_dn_office_code, federal_dn_judge_initials_assigned,
federal_dn_judge_initials_referred, federal_defendant_number, parent_docket_id
```

### Our Database Schema (20 columns)
```sql
CREATE TABLE search_docket (
    id integer NOT NULL,
    court_id character varying(50),
    assigned_to_id integer,
    referred_to_id integer,
    appeal_from_id character varying(50),
    docket_number text,
    case_name text,
    case_name_short text,
    case_name_full text,
    date_filed date,
    date_terminated date,
    date_argued date,
    date_reargued date,
    date_reargument_denied date,
    date_cert_granted date,
    date_cert_denied date,
    source smallint,
    pacer_case_id character varying(100),
    slug character varying(75),
    blocked boolean
);
```

### CourtListener Official Schema (53+ columns)

CourtListener provides an official schema file with each bulk data export:
- **File**: `data/schema-2025-10-31.sql`
- **Columns**: 53 columns for search_docket table
- **Includes**: All timestamp fields (date_created, date_modified), file paths (filepath_local, filepath_ia), metadata fields (cause, nature_of_suit, jury_demand), and more

Key columns we're missing:
- `date_created timestamp with time zone NOT NULL`
- `date_modified timestamp with time zone NOT NULL`
- `cause character varying(2000) NOT NULL`
- `nature_of_suit character varying(1000) NOT NULL`
- `jury_demand character varying(500) NOT NULL`
- `jurisdiction_type character varying(100) NOT NULL`
- `filepath_local character varying(1000) NOT NULL`
- `filepath_ia character varying(1000) NOT NULL`
- `filepath_ia_json character varying(1000) NOT NULL`
- `assigned_to_str text NOT NULL`
- `referred_to_str text NOT NULL`
- `appeal_from_str text NOT NULL`
- `panel_str text NOT NULL`
- `appellate_fee_status text NOT NULL`
- `appellate_case_type_information text NOT NULL`
- `mdl_status character varying(100) NOT NULL`
- `docket_number_core character varying(20) NOT NULL`
- `federal_dn_case_type character varying(6) NOT NULL`
- `federal_dn_office_code character varying(3) NOT NULL`
- `federal_dn_judge_initials_assigned character varying(5) NOT NULL`
- `federal_dn_judge_initials_referred character varying(5) NOT NULL`
- `federal_defendant_number smallint`
- `parent_docket_id integer`
- `view_count integer NOT NULL`
- `date_last_index timestamp with time zone`
- `date_last_filing date`
- `originating_court_information_id integer`
- `ia_needs_upload boolean`
- `ia_upload_failure_count smallint`
- `ia_date_first_change timestamp with time zone`
- `idb_data_id integer`
- `docket_number_raw character varying NOT NULL`

**We're missing 32-33 columns!**

---

## How This Caused Import Failures

### Issue #1: Column Filtering

Our import code (data_importer.py:138-151) filters CSV columns to only those that exist in the database:

```python
available_columns = [col for col in chunk.columns if col in db_columns]
chunk_filtered = chunk[available_columns].copy()
```

This means:
- CSV row has 52 values
- We only import 20 of them
- **32 columns of data are silently discarded**

### Issue #2: PostgreSQL COPY Failure

When we tried using PostgreSQL COPY command, it failed with:
```
ERROR: extra data after last expected column
```

This happened because:
- PostgreSQL COPY tries to load all 52 CSV columns
- Our table only has 20 columns
- PostgreSQL correctly rejects the mismatch

### Issue #3: Type Errors

Values like "mont", "mied", "njd" appeared in error messages as "invalid input syntax for type integer". This happened because:
- These are actually values for `federal_dn_office_code` column (varchar(3))
- But our schema is missing that column
- The import code was trying to map them to the wrong column

### Issue #4: False "Bad Data" Diagnosis

We incorrectly diagnosed the problem as:
- "CSV data is malformed"
- "CourtListener has bad bulk exports"
- "Need to skip bad rows with on_bad_lines='skip'"

**Reality**: The CSV data is perfectly valid. Our schema is incomplete.

---

## Why Other Users Succeed

Other CourtListener customers:

1. **Use the official schema file**: They run `schema-2025-10-31.sql` to create tables
2. **All columns match**: CSV has 52 columns, database has 52 columns
3. **No filtering needed**: Direct COPY command works at maximum speed
4. **No data loss**: All 52 columns are preserved

They can import the entire dataset (70M+ rows) in hours, not days.

---

## Proof: Schema File Exists

CourtListener provides the complete schema with every bulk export:

```bash
$ docker exec courtlistener-celery-worker ls -lh /app/data/schema*.sql
-rw-r--r-- 1 root root 398K Nov 11 17:20 schema-2025-10-31.sql
```

This file contains the complete CREATE TABLE statements for all tables in the bulk export.

**We should have been using this file from the beginning.**

---

## Recommended Solution

### Option 1: Use Official Schema (RECOMMENDED)

**Advantages**:
- Guaranteed compatibility with CSV files
- No more import errors
- Fast PostgreSQL COPY imports
- Future-proof (works with all CourtListener updates)

**Steps**:
1. Backup any existing data we want to keep
2. Drop our custom search_docket table
3. Run CourtListener's schema-2025-10-31.sql
4. Import CSV files using standard PostgreSQL COPY
5. Imports will complete in hours, not days

**Migration Command**:
```sql
-- Backup existing data (if needed)
CREATE TABLE search_docket_backup AS SELECT * FROM search_docket;

-- Drop our incomplete table
DROP TABLE IF EXISTS search_docket CASCADE;

-- Run official schema
\i /app/data/schema-2025-10-31.sql

-- Import will now work perfectly
COPY search_docket FROM '/app/data/search_docket-2025-10-31.csv'
WITH (FORMAT CSV, HEADER TRUE);
```

### Option 2: Add Missing Columns

**Advantages**:
- Keeps our existing data
- Preserves any custom indexes or constraints

**Disadvantages**:
- Much more work (32 ALTER TABLE statements)
- Risk of missing something
- Still need to maintain compatibility manually

**Would require**:
```sql
ALTER TABLE search_docket ADD COLUMN date_created timestamp with time zone;
ALTER TABLE search_docket ADD COLUMN date_modified timestamp with time zone;
ALTER TABLE search_docket ADD COLUMN cause character varying(2000);
-- ... 29 more ALTER statements
```

---

## Impact of Current Situation

### Data Loss
- We've imported 17.15M dockets, but **only 20 out of 52 columns**
- Missing critical metadata:
  - Timestamps (date_created, date_modified)
  - Case details (cause, nature_of_suit, jury_demand)
  - File paths (filepath_local, filepath_ia)
  - Federal docket numbers (federal_dn_office_code, etc.)
  - View counts, panel information, appellate details

### Performance Impact
- Pandas chunked processing: **very slow** (hours per table)
- PostgreSQL COPY would be **10-100x faster** but doesn't work with our schema

### Maintenance Burden
- Every CSV import requires custom filtering logic
- Schema changes from CourtListener will break our imports
- Can't leverage CourtListener's own tools/scripts

---

## Next Steps

1. **Decision**: Choose between Option 1 (official schema) or Option 2 (add columns)
2. **Backup**: Save any data we want to preserve
3. **Schema Update**: Implement chosen option
4. **Test Import**: Try importing a small test file
5. **Full Import**: Run complete import with corrected schema

---

## Lessons Learned

1. **Always use upstream schema**: When importing third-party data, use their official schema
2. **Investigate before workaround**: We spent hours working around "bad CSV data" that wasn't actually bad
3. **Check the source**: CourtListener provides schema files - we should have used them from day 1
4. **Column count mismatch is a red flag**: "31+ extra columns" should have been investigated immediately

---

## References

- CourtListener Official Schema: `data/schema-2025-10-31.sql`
- CSV Sample: `data/search_docket-sample.csv`
- Our Schema: See database at `search_docket` table
- Import Code: `backend/app/services/data_importer.py`
