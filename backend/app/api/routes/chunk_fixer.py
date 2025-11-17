"""
Chunk Fixer API Routes

Endpoint for fixing malformed CSV chunks with regex patterns.
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import logging
import re
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def fix_csv_line(line: str) -> str:
    """
    Fix common CSV formatting issues in a line.

    Args:
        line: Raw CSV line

    Returns:
        Fixed CSV line
    """
    # Replace sequences of 5+ quotes with properly escaped double quotes
    line = re.sub(r'"{5,}', '""', line)

    # Fix trailing quotes before commas or end of line
    line = re.sub(r'\\"+"(?=,|$)', '"', line)

    return line


def fix_chunk_file(chunk_path: Path) -> tuple:
    """
    Fix a single chunk file in place.

    Args:
        chunk_path: Path to chunk file

    Returns:
        Tuple of (lines_processed, lines_fixed)
    """
    logger.info(f"[FIX] Processing {chunk_path.name}...")

    # Read all lines
    with open(chunk_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # Fix each line (skip header)
    lines_fixed = 0
    fixed_lines = [lines[0]]  # Keep header as-is

    for i, line in enumerate(lines[1:], 1):
        fixed_line = fix_csv_line(line)
        if fixed_line != line:
            lines_fixed += 1
        fixed_lines.append(fixed_line)

    # Write back
    with open(chunk_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

    return len(lines), lines_fixed


@router.post("/fix-chunks")
async def fix_chunks(table_name: str, dataset_date: str = "2025-10-31"):
    """
    Fix malformed CSV chunks for a specific table/date.

    This endpoint applies regex patterns to fix common CSV formatting issues
    like multiple consecutive quotes and improperly escaped quotes.

    Args:
        table_name: Name of the table (e.g., "search_docket")
        dataset_date: Date string (default "2025-10-31")

    Returns:
        Dictionary with fix results
    """
    try:
        # Construct chunks directory path
        chunks_dir = Path(settings.DATA_DIR) / "chunks" / f"{table_name}-{dataset_date}"

        if not chunks_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Chunks directory not found: {chunks_dir}"
            )

        chunk_files = sorted(chunks_dir.glob("*.csv"))

        if not chunk_files:
            raise HTTPException(
                status_code=404,
                detail=f"No chunk files found in {chunks_dir}"
            )

        logger.info(f"[FIX] Found {len(chunk_files)} chunk files to fix")

        total_lines = 0
        total_fixed = 0
        fixed_chunks = []

        # Process ALL chunks
        for chunk_file in chunk_files:
            try:
                lines_processed, lines_fixed = fix_chunk_file(chunk_file)
                total_lines += lines_processed
                total_fixed += lines_fixed

                fixed_chunks.append({
                    "filename": chunk_file.name,
                    "lines_processed": lines_processed,
                    "lines_fixed": lines_fixed
                })

                logger.info(f"[FIX] ✓ {chunk_file.name}: {lines_processed:,} lines, {lines_fixed:,} fixed")

            except Exception as e:
                logger.error(f"[FIX] ✗ {chunk_file.name}: Error - {str(e)}")
                fixed_chunks.append({
                    "filename": chunk_file.name,
                    "error": str(e)
                })

        logger.info(f"[FIX] Complete: {total_lines:,} lines processed, {total_fixed:,} lines fixed")

        return {
            "status": "success",
            "table_name": table_name,
            "dataset_date": dataset_date,
            "chunks_directory": str(chunks_dir),
            "total_chunks": len(chunk_files),
            "total_lines_processed": total_lines,
            "total_lines_fixed": total_fixed,
            "chunks": fixed_chunks
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FIX] Error fixing chunks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
