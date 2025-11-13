"""
Service to identify and recover missing data from skipped CSV chunks.
"""
from pathlib import Path
from typing import Set, List, Dict
import pandas as pd
from sqlalchemy.orm import Session
from app.core.database import get_db


class MissingDataRecovery:
    """Identify and recover data that was skipped during import."""

    def __init__(self):
        self.chunk_size = 50000

    def get_imported_ids(self, db: Session, table_name: str) -> Set[int]:
        """Get all IDs currently in the database."""
        query = f"SELECT id FROM {table_name}"
        result = db.execute(query)
        return {row[0] for row in result}

    def get_csv_ids(self, csv_path: Path) -> Set[int]:
        """Get all IDs from the CSV file (just read the id column)."""
        print(f"Reading IDs from {csv_path}...")
        df = pd.read_csv(csv_path, usecols=['id'], dtype={'id': int})
        return set(df['id'].values)

    def find_missing_ids(self, db: Session, table_name: str, csv_path: Path) -> Set[int]:
        """Find IDs that are in CSV but not in database."""
        print(f"Finding missing IDs for {table_name}...")

        csv_ids = self.get_csv_ids(csv_path)
        db_ids = self.get_imported_ids(db, table_name)

        missing_ids = csv_ids - db_ids

        print(f"CSV has {len(csv_ids):,} records")
        print(f"Database has {len(db_ids):,} records")
        print(f"Missing: {len(missing_ids):,} records ({len(missing_ids)/len(csv_ids)*100:.2f}%)")

        return missing_ids

    def export_missing_rows(self, csv_path: Path, missing_ids: Set[int],
                           output_path: Path) -> int:
        """
        Read the full CSV and export only the rows with missing IDs.
        This creates a smaller CSV with just the data that needs to be re-imported.
        """
        print(f"Exporting missing rows to {output_path}...")

        rows_exported = 0
        first_chunk = True

        for chunk in pd.read_csv(csv_path, chunksize=self.chunk_size):
            # Filter to only rows with missing IDs
            missing_chunk = chunk[chunk['id'].isin(missing_ids)]

            if not missing_chunk.empty:
                # Write to output file
                missing_chunk.to_csv(
                    output_path,
                    mode='w' if first_chunk else 'a',
                    header=first_chunk,
                    index=False
                )
                rows_exported += len(missing_chunk)
                first_chunk = False

                if rows_exported % 100000 == 0:
                    print(f"  Exported {rows_exported:,} missing rows so far...")

        print(f"✓ Exported {rows_exported:,} missing rows to {output_path}")
        return rows_exported

    def generate_recovery_report(self, date: str = '2025-10-31') -> Dict[str, any]:
        """
        Generate a complete report of missing data for all case law tables.
        """
        tables = ['search_docket', 'search_opinioncluster',
                 'search_opinionscited', 'search_parenthetical']

        report = {}
        db = next(get_db())

        try:
            for table in tables:
                csv_path = Path(f'/app/data/{table}-{date}.csv')

                if not csv_path.exists():
                    print(f"Skipping {table} - CSV not found")
                    continue

                missing_ids = self.find_missing_ids(db, table, csv_path)

                report[table] = {
                    'missing_count': len(missing_ids),
                    'missing_ids': list(missing_ids)[:100]  # Sample of first 100
                }

                # Optionally export missing rows to a separate file
                if missing_ids:
                    output_path = Path(f'/app/data/{table}-{date}-MISSING.csv')
                    rows_exported = self.export_missing_rows(csv_path, missing_ids, output_path)
                    report[table]['recovery_file'] = str(output_path)
                    report[table]['rows_exported'] = rows_exported
        finally:
            db.close()

        return report


def generate_missing_data_report():
    """CLI command to generate missing data report."""
    recovery = MissingDataRecovery()
    report = recovery.generate_recovery_report()

    print("\n" + "="*60)
    print("MISSING DATA RECOVERY REPORT")
    print("="*60)

    for table, data in report.items():
        print(f"\n{table}:")
        print(f"  Missing records: {data['missing_count']:,}")
        if 'recovery_file' in data:
            print(f"  Recovery file: {data['recovery_file']}")
            print(f"  Rows exported: {data['rows_exported']:,}")

    return report


if __name__ == "__main__":
    generate_missing_data_report()
