# Services - Documentation

## Purpose
The `services` directory contains business logic services and external integrations. Services handle complex operations that don't belong in API routes or models.

## Services

### `s3_downloader.py` ✅ Implemented
**Purpose**: Downloads files from CourtListener's public S3 bucket.

**Key Components**:
- `CourtListenerDownloader` class
- Methods for listing available datasets
- Methods for downloading schema and CSV files
- File existence checking
- Automatic date extraction from filenames

**Key Methods**:
- `list_available_datasets()`: List all available bulk data files with metadata
- `get_available_dates()`: Get list of available dataset dates
- `get_files_for_date(date)`: Get all files for a specific date
- `download_schema(date)`: Download schema SQL file
- `download_csv(table_name, date)`: Download CSV file
- `download_dataset(date, tables)`: Download entire dataset (schema + CSV files)
- `file_exists_locally(filename)`: Check if file exists locally
- `get_file_size(key)`: Get file size from S3

**Dependencies**:
- `boto3` for S3 access (with unsigned config for public bucket)
- `app.core.config` for S3 configuration and data directory

**Usage**:
```python
from app.services.s3_downloader import CourtListenerDownloader

downloader = CourtListenerDownloader()
datasets = downloader.list_available_datasets()
downloader.download_csv('people_db_person', '2024-10-31')
downloaded = downloader.download_dataset('2024-10-31')
```

**Features**:
- Public bucket access (no credentials needed)
- Filters for People database tables
- Handles schema files, CSV files, and import scripts
- Returns file metadata (size, last modified, etc.)

### `data_importer.py` ✅ Implemented
**Purpose**: Imports CSV files into PostgreSQL database using pandas for robust CSV handling.

**Key Components**:
- Import order management (respects foreign key dependencies)
- Pandas-based CSV reading and import (handles malformed CSV files)
- Automatic column filtering (matches CSV columns to database schema)
- Error handling and validation
- Transaction management with rollback on failure
- ANALYZE execution after import
- Note: Table truncation temporarily disabled due to SIGSEGV issues

**Key Methods**:
- `import_csv(table_name, csv_path, db_session)`: Import single CSV file using pandas
- `import_dataset(date, tables, db_session)`: Import entire dataset in correct order
- `verify_files_exist(date, tables)`: Check if CSV files exist
- `get_table_row_count(table_name, db_session)`: Get row count for a table

**Import Method**:
- Uses pandas `read_csv()` with `on_bad_lines='skip'` and `engine='python'` for robust CSV parsing
- Automatically filters DataFrame columns to match database schema
- Uses pandas `to_sql()` with `method=None` (standard INSERT statements) instead of COPY
- Handles CSV files with unquoted carriage returns and other format issues

**Import Order** (defined in `IMPORT_ORDER`):
1. Courts (`people_db_court`)
2. People (`people_db_person`)
3. Schools (`people_db_school`)
4. Positions (`people_db_position`)
5. Education (`people_db_education`)
6. Political Affiliations (`people_db_politicalaffiliation`)
7. Races (`people_db_race`)
8. Sources (`people_db_source`)

**Dependencies**:
- Database session (SQLAlchemy)
- Models (for table names and structure)
- PostgreSQL COPY command (via SQL)

**Usage**:
```python
from app.services.data_importer import DataImporter
from app.core.database import SessionLocal

importer = DataImporter()
session = SessionLocal()

# Import entire dataset
results = importer.import_dataset('2024-10-31', db_session=session)

# Import single table
row_count = importer.import_csv('people_db_person', Path('./data/people_db_person-2024-10-31.csv'), session)
```

**Features**:
- Fast bulk import using PostgreSQL COPY
- Automatic dependency ordering
- Transaction-based (rollback on failure)
- Progress tracking via Celery tasks

### `data_validator.py` ✅ Implemented
**Purpose**: Validates data integrity after import.

**Key Components**:
- Foreign key constraint validation
- Data completeness checks
- Record count verification
- Data quality checks

**Key Methods**:
- `validate_foreign_keys(db_session)`: Check all foreign key relationships for orphaned records
- `validate_record_counts(expected_counts, db_session)`: Verify expected record counts match actual
- `validate_data_quality(db_session)`: Run data quality checks (missing names, invalid dates, etc.)
- `run_full_validation(db_session)`: Run all validation checks and return comprehensive results

**Dependencies**:
- Database session (SQLAlchemy)
- Models (for table structure)
- SQLAlchemy inspector (for constraint discovery)

**Usage**:
```python
from app.services.data_validator import DataValidator
from app.core.database import SessionLocal

validator = DataValidator()
session = SessionLocal()

# Run full validation
results = validator.run_full_validation(session)

# Validate specific checks
fk_results = validator.validate_foreign_keys(session)
quality_results = validator.validate_data_quality(session)
```

**Validation Checks**:
- Foreign key integrity (no orphaned records)
- Record counts (expected vs actual)
- Data quality (missing names, invalid date ranges, etc.)
- Completeness checks

## Dependencies
- **Depends on**: 
  - Database session (from `app.core.database`)
  - Configuration (from `app.core.config`)
  - Models (for database operations)
- **Used by**: 
  - API routes (via route handlers)
  - Celery tasks (for background processing)

## Integration
- Services are called from API routes
- Services can be used in Celery tasks for background processing
- Services use database sessions for data operations
- Services handle errors and return appropriate results

## Error Handling
- Services should raise appropriate exceptions
- Errors should be logged
- Services should provide meaningful error messages

## Reference
See [AI_INSTRUCTIONS.md](../../AI_INSTRUCTIONS.md) for complete application overview.

