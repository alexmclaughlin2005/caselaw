"""
Data Importer Service

Imports CSV files into PostgreSQL database using pandas for robust CSV handling.
Handles foreign key dependencies and import ordering.

Uses pandas instead of PostgreSQL COPY command to handle malformed CSV files
with unquoted carriage returns and other format issues.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import engine

logger = logging.getLogger(__name__)


class DataImporter:
    """
    Service for importing CSV files into PostgreSQL.
    
    Handles import ordering based on foreign key dependencies and uses
    PostgreSQL's COPY command for fast bulk imports.
    """
    
    # Import order based on foreign key dependencies
    IMPORT_ORDER = [
        # People database (foundation)
        "people_db_court",           # No dependencies
        "people_db_person",           # No dependencies
        "people_db_school",           # No dependencies
        "people_db_position",        # Depends on person, court
        "people_db_education",        # Depends on person, school
        "people_db_politicalaffiliation",  # Depends on person
        "people_db_race",            # Depends on person
        "people_db_source",          # Depends on person

        # Case law database (depends on people database)
        "search_docket",             # Depends on court, person
        "search_opinioncluster",     # Depends on docket
        "search_opinionscited",      # Citation map (self-referential, no FK constraints)
        "search_parenthetical",      # Depends on opinions (but we're not importing opinions yet)
    ]
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize data importer.
        
        Args:
            data_dir: Directory containing CSV files. Defaults to settings.DATA_DIR
        """
        self.data_dir = Path(data_dir) if data_dir else Path(settings.DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def import_csv_pandas(
        self,
        table_name: str,
        csv_path: Path,
        db_session: Optional[Session] = None,
        chunk_size: int = 100000,
        skip_self_referential_fk: bool = False
    ) -> int:
        """
        Import CSV using pandas with robust error handling for malformed CSVs.

        This method is specifically for CSVs with formatting issues like
        improperly escaped quotes in multi-line HTML/XML fields.

        Args:
            table_name: Name of the table to import into
            csv_path: Path to CSV file
            db_session: Optional database session
            chunk_size: Rows per chunk (default 100k)
            skip_self_referential_fk: If True, skip self-referential FK columns during import

        Returns:
            Number of rows imported
        """
        import pandas as pd
        from sqlalchemy import inspect

        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Use provided session or create new one
        if db_session:
            session = db_session
            should_close = False
        else:
            from app.core.database import SessionLocal
            session = SessionLocal()
            should_close = True

        try:
            logger.info(f"Importing {csv_path} into {table_name} using PANDAS robust parser")

            # Get database columns
            inspector = inspect(session.bind)
            db_columns = [c['name'] for c in inspector.get_columns(table_name)]

            count_before = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            logger.info(f"Current row count: {count_before:,}")

            # Read CSV in chunks with error handling
            total_imported = 0
            skipped_rows = 0
            chunk_num = 0

            # Increase CSV field size limit first
            import csv
            import sys
            maxInt = sys.maxsize
            while True:
                try:
                    csv.field_size_limit(maxInt)
                    break
                except OverflowError:
                    maxInt = int(maxInt/10)

            # Pandas parameters for robust CSV parsing
            csv_params = {
                'chunksize': chunk_size,
                'encoding': 'utf-8',
                'encoding_errors': 'replace',  # Replace invalid chars
                'on_bad_lines': 'warn',  # Warn but continue on bad lines
                'engine': 'python',  # Python engine is more flexible
                'quoting': 1,  # QUOTE_MINIMAL
                'escapechar': '\\',
                'doublequote': True,
                'na_values': ['', 'nan', 'NaN', 'NULL'],  # Treat these as NULL
                'keep_default_na': True,
            }

            logger.info(f"Processing CSV in {chunk_size:,} row chunks with pandas (robust mode)")

            for chunk_df in pd.read_csv(csv_path, **csv_params):
                chunk_num += 1

                # Filter to only columns that exist in database
                available_cols = [col for col in chunk_df.columns if col in db_columns]

                # Skip self-referential foreign key columns if requested
                if skip_self_referential_fk and table_name == "people_db_person":
                    available_cols = [col for col in available_cols if col != "is_alias_of_id"]

                chunk_df = chunk_df[available_cols]

                # Replace NaN and empty strings with None for proper NULL handling
                import numpy as np
                chunk_df = chunk_df.replace({np.nan: None, '': None, 'nan': None, 'NaN': None})

                # Convert to list of dicts
                chunk_rows = chunk_df.to_dict('records')

                # Batch insert with ON CONFLICT DO NOTHING
                columns = ', '.join([f'"{k}"' for k in available_cols])
                placeholders = ', '.join([f':{k}' for k in available_cols])

                insert_stmt = text(f"""
                    INSERT INTO {table_name} ({columns})
                    VALUES ({placeholders})
                    ON CONFLICT (id) DO NOTHING
                """)

                try:
                    session.execute(insert_stmt, chunk_rows)
                    total_imported += len(chunk_rows)
                except Exception as e:
                    session.rollback()
                    logger.warning(f"Skipping chunk {chunk_num} due to error: {str(e)[:200]}")
                    skipped_rows += len(chunk_rows)
                    continue

                # Commit every 10 chunks
                if chunk_num % 10 == 0:
                    session.commit()
                    current_count = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                    logger.info(f"Progress: Processed {chunk_num} chunks ({total_imported:,} rows, {skipped_rows:,} skipped) - Database total: {current_count:,}")

            # Final commit
            session.commit()
            count_after = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

            logger.info(f"Import complete: {count_after - count_before:,} new rows added")
            logger.info(f"Total skipped: {skipped_rows:,}")

            return total_imported

        finally:
            if should_close:
                session.close()

    def import_csv(
        self,
        table_name: str,
        csv_path: Path,
        db_session: Optional[Session] = None
    ) -> int:
        """
        Import a single CSV file into a table using PostgreSQL COPY.

        Args:
            table_name: Name of the table to import into
            csv_path: Path to CSV file
            db_session: Optional database session (creates new if not provided)

        Returns:
            Number of rows imported
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Use provided session or create new one
        if db_session:
            session = db_session
            should_close = False
        else:
            from app.core.database import SessionLocal
            session = SessionLocal()
            should_close = True

        try:
            # Get absolute path for COPY command
            abs_path = csv_path.resolve()

            logger.info(f"Importing {csv_path} into {table_name}")

            # Use pandas to read CSV (handles malformed CSV better) then insert via SQLAlchemy
            # This avoids COPY format issues with unquoted carriage returns
            import pandas as pd

            # Get row count before import
            count_before = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

            logger.info(f"Reading CSV file with ROBUST parser (handles multi-line fields): {abs_path}")

            # Get actual table columns from database first
            table_columns_result = session.execute(text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
            """))
            db_columns = [row[0] for row in table_columns_result]

            # Use chunked reading to avoid memory issues with large files
            chunk_size = 100000  # Process 100k rows at a time (optimized for speed)
            total_rows_imported = 0
            chunk_num = 0

            logger.info(f"Processing CSV in chunks of {chunk_size} rows using Python csv module")

            # Use Python's native csv module which handles multi-line quoted fields correctly
            # CourtListener CSVs have HTML/XML in quoted fields with embedded newlines
            # pandas csv parser fails on these, but Python's csv module handles them properly
            import csv
            import sys

            # Increase CSV field size limit to handle very large HTML/XML fields
            # Some headmatter fields exceed the default 128KB limit
            maxInt = sys.maxsize
            while True:
                try:
                    csv.field_size_limit(maxInt)
                    break
                except OverflowError:
                    maxInt = int(maxInt/10)

            # Open file and create CSV reader
            try:
                csv_file = open(abs_path, 'r', encoding='utf-8', errors='replace')
                csv_reader = csv.reader(csv_file, quoting=csv.QUOTE_MINIMAL)

                # Read header
                header = next(csv_reader)
                expected_cols = len(header)

                # Validate columns
                available_columns = [col for col in header if col in db_columns]
                missing_columns = [col for col in header if col not in db_columns]

                if missing_columns:
                    logger.warning(f"CSV has columns not in database table {table_name}: {missing_columns}. These will be skipped.")

                if not available_columns:
                    raise ValueError(f"No matching columns between CSV and database table {table_name}")

                logger.info(f"Importing {len(available_columns)} columns: {', '.join(available_columns[:10])}{'...' if len(available_columns) > 10 else ''}")

                # Create column index mapping for available columns
                col_indices = {col: header.index(col) for col in available_columns}

                # Boolean and date column names for conversion
                boolean_columns = {'blocked', 'ia_needs_upload'}
                date_columns = {'date_created', 'date_modified', 'date_filed', 'date_terminated',
                               'date_argued', 'date_reargued', 'date_reargument_denied',
                               'date_cert_granted', 'date_cert_denied', 'date_last_index',
                               'date_last_filing', 'date_blocked', 'ia_date_first_change'}

                # Process CSV in chunks
                chunk_rows = []
                row_num = 0
                skipped_rows = 0

                for row in csv_reader:
                    row_num += 1

                    # Skip rows with incorrect column count (malformed CSV)
                    if len(row) != expected_cols:
                        skipped_rows += 1
                        continue

                    # Extract and validate row data with row-level validation
                    try:
                        row_dict = {}
                        for col in available_columns:
                            idx = col_indices[col]
                            value = row[idx]

                            # Convert empty strings to None
                            if value == '':
                                value = None
                            # Convert boolean strings
                            elif col in boolean_columns and value in ('t', 'f'):
                                value = (value == 't')
                            # Convert invalid date values
                            elif col in date_columns and value == '0':
                                value = None

                            row_dict[col] = value

                        # Minimal validation: only check that ID exists and is valid
                        # Let PostgreSQL handle type validation for other fields
                        # This avoids rejecting valid legal data with complex formatting
                        if 'id' in row_dict and row_dict['id'] is not None:
                            try:
                                int(row_dict['id'])
                            except (ValueError, TypeError):
                                raise ValueError(f"Invalid ID value: {row_dict['id']}")

                        # Row is valid - add to chunk
                        chunk_rows.append(row_dict)

                    except (ValueError, TypeError) as e:
                        # Skip individual malformed rows (row-level validation)
                        skipped_rows += 1
                        if skipped_rows % 10000 == 0:  # Log every 10K skipped rows
                            logger.warning(f"Skipped {skipped_rows:,} malformed rows so far (last error: {str(e)[:100]})")
                        continue

                    # Process chunk when it reaches chunk_size (outside try-except)
                    if len(chunk_rows) >= chunk_size:
                        chunk_num += 1

                        # Batch insert using ON CONFLICT DO NOTHING
                        columns = ', '.join([f'"{k}"' for k in available_columns])
                        placeholders = ', '.join([f':{k}' for k in available_columns])

                        insert_stmt = text(f"""
                            INSERT INTO {table_name} ({columns})
                            VALUES ({placeholders})
                            ON CONFLICT (id) DO NOTHING
                        """)

                        try:
                            session.execute(insert_stmt, chunk_rows)
                            total_rows_imported += len(chunk_rows)
                        except Exception as e:
                            # Rollback failed transaction to allow subsequent chunks to proceed
                            session.rollback()
                            logger.warning(f"Skipping chunk {chunk_num} due to error: {str(e)[:200]}")

                        # Commit every 10 chunks (1M rows) for better progress visibility
                        if chunk_num % 10 == 0:
                            session.commit()
                            current_count = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                            logger.info(f"Progress: Processed {chunk_num} chunks ({total_rows_imported:,} rows, {skipped_rows:,} skipped) - Database total: {current_count:,}")

                        # Reset chunk
                        chunk_rows = []

                # Process remaining rows
                if chunk_rows:
                    chunk_num += 1
                    columns = ', '.join([f'"{k}"' for k in available_columns])
                    placeholders = ', '.join([f':{k}' for k in available_columns])

                    insert_stmt = text(f"""
                        INSERT INTO {table_name} ({columns})
                        VALUES ({placeholders})
                        ON CONFLICT (id) DO NOTHING
                    """)

                    try:
                        session.execute(insert_stmt, chunk_rows)
                        total_rows_imported += len(chunk_rows)
                    except Exception as e:
                        # Rollback failed transaction to allow final commit
                        session.rollback()
                        logger.warning(f"Skipping final chunk due to error: {str(e)[:200]}")

                # Final commit
                session.commit()

                # Get row count after import
                count_after = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                row_count = count_after - count_before

                logger.info(f"Imported {row_count:,} rows into {table_name} (total: {count_after:,}, skipped {skipped_rows:,} malformed rows)")

                return row_count

            finally:
                if 'csv_file' in locals():
                    csv_file.close()

        except Exception as e:
            logger.error(f"Error importing {csv_path} into {table_name}: {str(e)}")
            raise
        finally:
            if should_close:
                session.close()
    
    def import_csv_with_postgres_copy(
        self,
        table_name: str,
        csv_path: Path,
        db_session: Optional[Session] = None
    ) -> int:
        """
        Import a single CSV file using PostgreSQL's native COPY command.

        This method uses PostgreSQL's COPY FROM command which is 10-100x faster
        than pandas to_sql() for bulk imports. It reads directly from the CSV file
        on disk without loading it into memory.

        Args:
            table_name: Name of the table to import into
            csv_path: Path to CSV file
            db_session: Optional database session (creates new if not provided)

        Returns:
            Number of rows imported
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Use provided session or create new one
        if db_session:
            session = db_session
            should_close = False
        else:
            from app.core.database import SessionLocal
            session = SessionLocal()
            should_close = True

        try:
            import time
            abs_path = csv_path.resolve()
            logger.info(f"Importing {csv_path} into {table_name} using PostgreSQL COPY (ultra-fast)")

            # Get row count before import
            count_before = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

            start_time = time.time()

            # Use PostgreSQL COPY command for maximum speed
            # COPY is the fastest way to bulk load data into PostgreSQL
            copy_sql = text(f"""
                COPY {table_name}
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    HEADER TRUE,
                    DELIMITER ',',
                    NULL '',
                    QUOTE '"',
                    ESCAPE '"'
                )
            """)

            # Get raw connection for COPY
            raw_conn = session.connection().connection
            cursor = raw_conn.cursor()

            # Create temporary table for staging
            temp_table = f"{table_name}_temp_import"
            cursor.execute(f"CREATE TEMP TABLE {temp_table} (LIKE {table_name} INCLUDING DEFAULTS)")

            # Load CSV into temporary table
            with open(abs_path, 'r', encoding='utf-8') as f:
                cursor.copy_expert(f"COPY {temp_table} FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',', NULL '', QUOTE '\"', ESCAPE '\"')", f)

            # Insert from temp table, skipping duplicates based on ID
            cursor.execute(f"""
                INSERT INTO {table_name}
                SELECT * FROM {temp_table}
                ON CONFLICT (id) DO NOTHING
            """)

            # Drop temp table
            cursor.execute(f"DROP TABLE {temp_table}")

            session.commit()
            elapsed = time.time() - start_time

            # Get row count after import
            count_after = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            row_count = count_after - count_before

            rate = row_count / elapsed if elapsed > 0 else 0
            logger.info(f"Imported {row_count:,} rows into {table_name} in {elapsed:.1f}s ({rate:,.0f} rows/sec) - Total: {count_after:,}")

            return row_count

        except Exception as e:
            logger.error(f"Error importing {csv_path} into {table_name} with PostgreSQL COPY: {str(e)}")
            if not should_close and session:
                session.rollback()
            raise
        finally:
            if should_close:
                session.close()

    def import_dataset(
        self,
        date: str,
        tables: Optional[List[str]] = None,
        db_session: Optional[Session] = None
    ) -> Dict[str, int]:
        """
        Import an entire dataset in the correct dependency order.
        
        Args:
            date: Date string (YYYY-MM-DD) of the dataset
            tables: Optional list of table names to import. If None, imports all.
            db_session: Optional database session
            
        Returns:
            Dictionary mapping table names to number of rows imported
        """
        if tables is None:
            tables = self.IMPORT_ORDER
        
        # Filter to only tables that exist in IMPORT_ORDER
        tables_to_import = [t for t in tables if t in self.IMPORT_ORDER]
        # Sort by IMPORT_ORDER
        tables_to_import.sort(key=lambda x: self.IMPORT_ORDER.index(x))
        
        results = {}
        
        # Use provided session or create new
        if db_session:
            session = db_session
            should_close = False
        else:
            from app.core.database import SessionLocal
            session = SessionLocal()
            should_close = True
        
        try:
            # Skip truncation for now due to segmentation fault issues
            # TODO: Investigate and fix the SIGSEGV during TRUNCATE in Celery workers
            # For now, we'll import directly (first import) or handle duplicates separately
            logger.info("Skipping truncation - importing directly (will handle duplicates if needed)")
            
            # Import tables in dependency order
            logger.info(f"Starting import for date {date}")

            # Define large tables that should use chunked pandas (handles malformed CSV data)
            large_tables = ['search_docket', 'search_opinioncluster', 'search_opinionscited', 'search_parenthetical']

            for table_name in tables_to_import:
                csv_filename = f"{table_name}-{date}.csv"
                csv_path = self.data_dir / csv_filename

                if not csv_path.exists():
                    logger.warning(f"CSV file not found: {csv_path}, skipping")
                    results[table_name] = 0
                    continue

                try:
                    # Use chunked pandas for ALL tables (handles malformed CSV better than COPY)
                    # The optimized PostgreSQL settings still help with bulk inserts
                    logger.info(f"Using chunked pandas import for table {table_name}")
                    row_count = self.import_csv(table_name, csv_path, session)

                    results[table_name] = row_count
                    session.commit()
                except Exception as e:
                    logger.error(f"Failed to import {table_name}: {str(e)}")
                    session.rollback()
                    results[table_name] = 0
                    raise
            
            # Run ANALYZE on all imported tables
            logger.info("Running ANALYZE on imported tables")
            for table_name in tables_to_import:
                try:
                    session.execute(text(f"ANALYZE {table_name}"))
                except Exception as e:
                    logger.warning(f"Could not analyze {table_name}: {str(e)}")
            
            session.commit()
            
            logger.info(f"Import completed for date {date}")
            return results
            
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            session.rollback()
            raise
        finally:
            if should_close:
                session.close()
    
    def verify_files_exist(self, date: str, tables: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Verify that CSV files exist for a dataset.
        
        Args:
            date: Date string (YYYY-MM-DD)
            tables: Optional list of table names to check
            
        Returns:
            Dictionary mapping table names to whether file exists
        """
        if tables is None:
            tables = self.IMPORT_ORDER
        
        results = {}
        for table_name in tables:
            csv_filename = f"{table_name}-{date}.csv"
            csv_path = self.data_dir / csv_filename
            results[table_name] = csv_path.exists()
        
        return results
    
    def get_table_row_count(self, table_name: str, db_session: Optional[Session] = None) -> int:
        """
        Get the current row count for a table.
        
        Args:
            table_name: Name of the table
            db_session: Optional database session
            
        Returns:
            Number of rows in the table
        """
        if db_session:
            result = db_session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
        else:
            from app.core.database import SessionLocal
            session = SessionLocal()
            try:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.scalar()
            finally:
                session.close()

