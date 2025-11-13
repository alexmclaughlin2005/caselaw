"""add_date_blocked_column

Revision ID: cf47bd255dfb
Revises: 479568b90b61
Create Date: 2025-11-11 21:51:15.534849

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf47bd255dfb'
down_revision = '479568b90b61'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing date_blocked column to search_docket table."""

    # Add date_blocked column (nullable date type)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS date_blocked date;
    """)

    print("✓ Added date_blocked column to search_docket table")
    print("  Column is nullable to match CSV data (many NULL values)")


def downgrade() -> None:
    """Remove date_blocked column (for rollback)."""

    op.execute("""
        ALTER TABLE search_docket
        DROP COLUMN IF EXISTS date_blocked;
    """)

    print("✓ Removed date_blocked column from search_docket table")

