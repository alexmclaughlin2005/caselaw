"""
Data Management Schemas

Pydantic schemas for data download and import operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class DatasetInfo(BaseModel):
    """Information about an available dataset."""
    key: str
    date: str
    type: str  # 'schema', 'csv', 'script', 'other'
    table_name: Optional[str] = None
    size: int
    last_modified: str


class AvailableDatasetsResponse(BaseModel):
    """Response containing available datasets."""
    datasets: List[DatasetInfo]
    dates: List[str]  # Unique dates available


class DownloadRequest(BaseModel):
    """Request to download files."""
    date: str = Field(..., description="Date string (YYYY-MM-DD)")
    tables: Optional[List[str]] = Field(
        None,
        description="List of table names to download. If None, downloads all people tables."
    )
    include_schema: bool = Field(True, description="Whether to download schema file")


class DownloadStatus(BaseModel):
    """Status of a download operation."""
    status: str  # 'pending', 'downloading', 'completed', 'failed'
    date: str
    files: Dict[str, Dict] = Field(
        default_factory=dict,
        description="Dictionary mapping file names to their download status"
    )
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Overall progress (0.0 to 1.0)")
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class FileDownloadStatus(BaseModel):
    """Status of a single file download."""
    filename: str
    status: str  # 'pending', 'downloading', 'completed', 'failed'
    bytes_downloaded: int = 0
    total_bytes: Optional[int] = None
    progress: float = Field(0.0, ge=0.0, le=1.0)
    error: Optional[str] = None


class DatabaseStatus(BaseModel):
    """Current database status."""
    # People database
    total_people: int = 0
    total_positions: int = 0
    total_schools: int = 0
    total_educations: int = 0

    # Case law database
    total_dockets: int = 0
    total_opinion_clusters: int = 0
    total_citations: int = 0
    total_parentheticals: int = 0

    last_import_date: Optional[str] = None
    last_import_status: Optional[str] = None
    database_size_mb: Optional[float] = None


class ImportRequest(BaseModel):
    """Request to import data."""
    date: str = Field(..., description="Date string (YYYY-MM-DD) of dataset to import")
    tables: Optional[List[str]] = Field(
        None,
        description="List of table names to import. If None, imports all people tables."
    )


class ImportStatus(BaseModel):
    """Status of an import operation."""
    status: str  # 'pending', 'importing', 'completed', 'failed'
    date: str
    current_table: Optional[str] = None
    tables_completed: List[str] = Field(default_factory=list)
    tables_total: int = 0
    progress: float = Field(0.0, ge=0.0, le=1.0)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    records_imported: Dict[str, int] = Field(
        default_factory=dict,
        description="Number of records imported per table"
    )


class ValidationRequest(BaseModel):
    """Request to validate data."""
    check_foreign_keys: bool = True
    check_record_counts: bool = True
    check_data_quality: bool = True


class ValidationResult(BaseModel):
    """Result of data validation."""
    passed: bool
    checks: Dict[str, Dict] = Field(
        default_factory=dict,
        description="Results of individual validation checks"
    )
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class TableImportProgress(BaseModel):
    """Progress information for a single table."""
    table_name: str
    current_count: int
    expected_count: int
    status: str  # 'pending', 'importing', 'completed'
    progress_percent: float = Field(0.0, ge=0.0, le=100.0)


class ImportProgressResponse(BaseModel):
    """Real-time import progress for all case law tables."""
    search_docket: TableImportProgress
    search_opinioncluster: TableImportProgress
    search_opinionscited: TableImportProgress
    search_parenthetical: TableImportProgress

