"""
S3 Downloader Service

Downloads files from CourtListener's public S3 bucket.
No authentication required - bucket is publicly accessible.
"""
import os
import re
import bz2
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import boto3
from botocore import UNSIGNED
from botocore.client import Config
from botocore.exceptions import ClientError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class CourtListenerDownloader:
    """
    Service for downloading files from CourtListener's S3 bucket.
    
    The bucket is publicly accessible, so no AWS credentials are needed.
    """
    
    BUCKET_NAME = "com-courtlistener-storage"
    PREFIX = "bulk-data/"
    
    # People database table names we're interested in (database table names)
    PEOPLE_TABLES = [
        "people_db_person",
        "people_db_position",
        "people_db_school",
        "people_db_education",
        "people_db_politicalaffiliation",
        "people_db_race",
        "people_db_source",
        "people_db_abarating",
        "people_db_retentionevent",
    ]

    # Case law database table names
    CASE_LAW_TABLES = [
        "search_docket",
        "search_opinioncluster",
        "search_opinionscited",  # Citation map
        "search_parenthetical",
    ]

    # Mapping from S3 file names to database table names
    # S3 uses: people-db-{plural-name}-{date}.csv.bz2 or courts-{date}.csv.bz2
    # DB uses: people_db_{singular_name}
    S3_TO_DB_TABLE_MAP = {
        # People database
        "people-db-people": "people_db_person",
        "people-db-positions": "people_db_position",
        "people-db-schools": "people_db_school",
        "people-db-educations": "people_db_education",
        "people-db-political-affiliations": "people_db_politicalaffiliation",
        "people-db-races": "people_db_race",
        "people-db-sources": "people_db_source",
        "people-db-retention-events": "people_db_retentionevent",
        "courts": "people_db_court",  # Courts are in separate file

        # Case law database
        "dockets": "search_docket",
        "opinion-clusters": "search_opinioncluster",
        "citation-map": "search_opinionscited",
        "parentheticals": "search_parenthetical",
    }
    
    def __init__(self):
        """Initialize S3 client with unsigned config for public bucket."""
        self.s3 = boto3.client(
            's3',
            config=Config(signature_version=UNSIGNED)
        )
        self.data_dir = Path(settings.DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def list_available_datasets(self) -> List[Dict]:
        """
        List all available bulk data files with dates.
        
        Returns:
            List of dictionaries containing file information:
            {
                'key': str,           # S3 object key
                'date': str,           # Extracted date (YYYY-MM-DD)
                'type': str,           # 'schema', 'csv', 'script', or 'other'
                'table_name': str,     # Table name for CSV files (if applicable)
                'size': int,           # File size in bytes
                'last_modified': str   # Last modified timestamp
            }
        """
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.BUCKET_NAME,
                Prefix=self.PREFIX
            )
            
            datasets = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                
                # Extract date from filename (format: YYYY-MM-DD)
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', key)
                if not date_match:
                    continue
                
                date_str = date_match.group(1)
                
                # Determine file type
                file_info = self._parse_file_info(key, date_str)
                if file_info:
                    file_info.update({
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                    })
                    datasets.append(file_info)
            
            # Sort by date (newest first)
            datasets.sort(key=lambda x: x['date'], reverse=True)
            
            return datasets
            
        except ClientError as e:
            raise Exception(f"Error listing S3 objects: {str(e)}")
    
    def _parse_file_info(self, key: str, date: str) -> Optional[Dict]:
        """
        Parse file information from S3 key.
        
        Args:
            key: S3 object key
            date: Extracted date string
            
        Returns:
            Dictionary with file info or None if not relevant
        """
        filename = os.path.basename(key)
        
        # Schema file
        if 'schema' in filename.lower():
            return {
                'key': key,
                'date': date,
                'type': 'schema',
                'table_name': None,
            }
        
        # Import script
        if filename.endswith('.sh') and 'load' in filename.lower():
            return {
                'key': key,
                'date': date,
                'type': 'script',
                'table_name': None,
            }
        
        # CSV files - check if it's a people table or courts (supports both .csv and .csv.bz2)
        if filename.endswith('.csv') or filename.endswith('.csv.bz2'):
            # Check for courts file: courts-{date}.csv.bz2
            courts_match = re.match(r'courts-\d{4}-\d{2}-\d{2}\.csv(\.bz2)?', filename)
            if courts_match:
                db_table_name = self.S3_TO_DB_TABLE_MAP.get("courts")
                if db_table_name:
                    return {
                        'key': key,
                        'date': date,
                        'type': 'csv',
                        'table_name': db_table_name,
                        's3_name': 'courts',
                        'compressed': filename.endswith('.bz2'),
                    }
            
            # Extract table name from S3 naming pattern: people-db-{name}-{date}.csv.bz2
            # or old pattern: people_db_{name}-{date}.csv
            table_match = re.match(r'(people-db-[a-z-]+)-\d{4}-\d{2}-\d{2}\.csv(\.bz2)?', filename)
            if table_match:
                s3_table_name = table_match.group(1)
                # Map S3 name to database table name
                db_table_name = self.S3_TO_DB_TABLE_MAP.get(s3_table_name)
                if db_table_name:
                    return {
                        'key': key,
                        'date': date,
                        'type': 'csv',
                        'table_name': db_table_name,
                        's3_name': s3_table_name,
                        'compressed': filename.endswith('.bz2'),
                    }

            # Check for case law files: dockets-{date}.csv.bz2, opinion-clusters-{date}.csv.bz2, etc.
            caselaw_match = re.match(r'(dockets|opinion-clusters|citation-map|parentheticals)-\d{4}-\d{2}-\d{2}\.csv(\.bz2)?', filename)
            if caselaw_match:
                s3_table_name = caselaw_match.group(1)
                db_table_name = self.S3_TO_DB_TABLE_MAP.get(s3_table_name)
                if db_table_name:
                    return {
                        'key': key,
                        'date': date,
                        'type': 'csv',
                        'table_name': db_table_name,
                        's3_name': s3_table_name,
                        'compressed': filename.endswith('.bz2'),
                    }

            # Also check old pattern for backwards compatibility
            old_match = re.match(r'(people_db_[a-z_]+)-\d{4}-\d{2}-\d{2}\.csv', filename)
            if old_match:
                table_name = old_match.group(1)
                if table_name in self.PEOPLE_TABLES or table_name == "people_db_court":
                    return {
                        'key': key,
                        'date': date,
                        'type': 'csv',
                        'table_name': table_name,
                        'compressed': False,
                    }
        
        return None
    
    def get_available_dates(self) -> List[str]:
        """
        Get list of available dataset dates.
        
        Returns:
            List of date strings (YYYY-MM-DD) sorted newest first
        """
        datasets = self.list_available_datasets()
        dates = sorted(set(d['date'] for d in datasets), reverse=True)
        return dates
    
    def get_files_for_date(self, date: str) -> Dict[str, List[Dict]]:
        """
        Get all files available for a specific date.
        
        Args:
            date: Date string (YYYY-MM-DD)
            
        Returns:
            Dictionary with keys: 'schema', 'csv', 'script'
            Each contains list of file info dicts
        """
        datasets = self.list_available_datasets()
        date_files = {
            'schema': [],
            'csv': [],
            'script': [],
        }
        
        for dataset in datasets:
            if dataset['date'] == date:
                file_type = dataset['type']
                if file_type in date_files:
                    date_files[file_type].append(dataset)
        
        return date_files
    
    def download_file(self, key: str, target_path: Optional[Path] = None) -> Path:
        """
        Download a file from S3 and decompress if needed.
        
        Args:
            key: S3 object key
            target_path: Optional target path. If not provided, uses data_dir
            
        Returns:
            Path to downloaded (and decompressed) file
        """
        filename = os.path.basename(key)
        is_compressed = filename.endswith('.bz2')
        
        # Determine target path
        if target_path is None:
            # Remove .bz2 extension if compressed, keep .csv
            if is_compressed:
                base_name = filename.replace('.bz2', '')
                target_path = self.data_dir / base_name
            else:
                target_path = self.data_dir / filename
        else:
            # If target_path provided but file is compressed, ensure .csv extension
            if is_compressed and target_path.suffix == '.bz2':
                target_path = target_path.with_suffix('')
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if is_compressed:
                # Download compressed file to temp location, then decompress
                temp_path = target_path.with_suffix(target_path.suffix + '.bz2')
                self.s3.download_file(
                    self.BUCKET_NAME,
                    key,
                    str(temp_path)
                )
                # Decompress in chunks to avoid memory issues with large files
                with bz2.open(temp_path, 'rb') as f_in:
                    with open(target_path, 'wb') as f_out:
                        # Stream decompression in 100MB chunks
                        chunk_size = 100 * 1024 * 1024  # 100MB
                        while True:
                            chunk = f_in.read(chunk_size)
                            if not chunk:
                                break
                            f_out.write(chunk)
                # Remove temp compressed file
                temp_path.unlink()
                logger.info(f"Downloaded and decompressed {key} to {target_path}")
            else:
                # Download uncompressed file directly
                self.s3.download_file(
                    self.BUCKET_NAME,
                    key,
                    str(target_path)
                )
                logger.info(f"Downloaded {key} to {target_path}")
            
            return target_path
        except ClientError as e:
            raise Exception(f"Error downloading {key}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing {key}: {str(e)}")
    
    def download_schema(self, date: str) -> Path:
        """
        Download schema SQL file for a specific date.
        
        Args:
            date: Date string (YYYY-MM-DD)
            
        Returns:
            Path to downloaded schema file
        """
        files = self.get_files_for_date(date)
        if not files['schema']:
            raise ValueError(f"No schema file found for date {date}")
        
        schema_file = files['schema'][0]
        target_path = self.data_dir / f"schema-{date}.sql"
        
        return self.download_file(schema_file['key'], target_path)
    
    def download_csv(self, table_name: str, date: str) -> Path:
        """
        Download CSV file for a specific table and date.
        
        Args:
            table_name: Table name (e.g., 'people_db_person')
            date: Date string (YYYY-MM-DD)
            
        Returns:
            Path to downloaded CSV file
        """
        files = self.get_files_for_date(date)
        csv_files = files['csv']
        
        # Find the matching table
        matching_file = None
        for csv_file in csv_files:
            if csv_file['table_name'] == table_name:
                matching_file = csv_file
                break
        
        if not matching_file:
            raise ValueError(f"No CSV file found for table {table_name} on date {date}")
        
        target_path = self.data_dir / f"{table_name}-{date}.csv"
        
        return self.download_file(matching_file['key'], target_path)
    
    def download_dataset(self, date: str, tables: Optional[List[str]] = None) -> Dict[str, Path]:
        """
        Download all files for a dataset (schema + CSV files).

        Args:
            date: Date string (YYYY-MM-DD)
            tables: Optional list of table names to download.
                   If None, downloads all people tables, courts, and case law tables.

        Returns:
            Dictionary mapping file type/name to downloaded path
        """
        if tables is None:
            # Include all people tables plus courts plus case law tables
            tables = self.PEOPLE_TABLES + ["people_db_court"] + self.CASE_LAW_TABLES
        
        downloaded = {}
        
        # Download schema
        try:
            schema_path = self.download_schema(date)
            downloaded['schema'] = schema_path
        except ValueError:
            pass  # Schema might not exist for all dates
        
        # Download CSV files
        for table_name in tables:
            try:
                csv_path = self.download_csv(table_name, date)
                downloaded[table_name] = csv_path
            except ValueError as e:
                # Log but continue with other tables
                logger.warning(f"Warning: {e}")
        
        return downloaded
    
    def file_exists_locally(self, filename: str) -> bool:
        """
        Check if a file exists in the local data directory.
        
        Args:
            filename: Name of the file
            
        Returns:
            True if file exists, False otherwise
        """
        file_path = self.data_dir / filename
        return file_path.exists()
    
    def get_file_size(self, key: str) -> int:
        """
        Get the size of a file in S3.
        
        Args:
            key: S3 object key
            
        Returns:
            File size in bytes
        """
        try:
            response = self.s3.head_object(
                Bucket=self.BUCKET_NAME,
                Key=key
            )
            return response['ContentLength']
        except ClientError as e:
            raise Exception(f"Error getting file size for {key}: {str(e)}")

