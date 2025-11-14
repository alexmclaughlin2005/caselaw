"""
CSV Chunk Progress Model

Tracks the progress of chunked CSV imports to enable resumable imports
and detailed progress monitoring.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, BigInteger
from sqlalchemy.sql import func
from app.core.database import Base


class CSVChunkProgress(Base):
    """
    Model for tracking CSV chunk import progress.

    Enables:
    - Resumable imports (restart from last successful chunk)
    - Detailed progress tracking per chunk
    - Error logging per chunk
    - Historical import records
    """
    __tablename__ = "csv_chunk_progress"

    id = Column(Integer, primary_key=True, index=True)

    # Chunk identification
    table_name = Column(String(100), nullable=False, index=True)
    dataset_date = Column(String(20), nullable=False, index=True)  # e.g., "2025-10-31"
    chunk_number = Column(Integer, nullable=False, index=True)
    chunk_filename = Column(String(255), nullable=False)

    # Chunk metadata
    chunk_start_row = Column(BigInteger, nullable=True)  # Starting row number in original CSV
    chunk_end_row = Column(BigInteger, nullable=True)    # Ending row number in original CSV
    chunk_row_count = Column(BigInteger, nullable=True)  # Actual rows in this chunk

    # Import status
    status = Column(String(20), nullable=False, default="pending", index=True)
    # Status values: pending, processing, completed, failed, skipped

    # Import results
    rows_imported = Column(BigInteger, nullable=True, default=0)
    rows_skipped = Column(BigInteger, nullable=True, default=0)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

    # Import method used
    import_method = Column(String(50), nullable=True)  # e.g., "standard", "pandas", "copy"

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<CSVChunkProgress(table={self.table_name}, chunk={self.chunk_number}, status={self.status})>"
