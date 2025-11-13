"""fix_nullable_columns_in_search_docket

Revision ID: 479568b90b61
Revises: bc02f0ddd58f
Create Date: 2025-11-11 21:18:23.735251

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '479568b90b61'
down_revision = 'bc02f0ddd58f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make columns nullable that have NULL values in CSV data."""

    # The CSV data contains NULL/empty values for many of the newly added columns
    # These columns need to be nullable to allow the data to import successfully

    # Text/varchar columns that should be nullable (empty in CSV = NULL in pandas)
    nullable_text_columns = [
        'cause', 'nature_of_suit', 'jury_demand', 'jurisdiction_type',
        'filepath_local', 'filepath_ia', 'filepath_ia_json',
        'assigned_to_str', 'referred_to_str', 'appeal_from_str', 'panel_str',
        'appellate_fee_status', 'appellate_case_type_information',
        'mdl_status', 'docket_number_core', 'federal_dn_case_type',
        'federal_dn_judge_initials_assigned', 'federal_dn_judge_initials_referred',
        'federal_dn_office_code', 'docket_number_raw'
    ]

    for column in nullable_text_columns:
        op.execute(f"""
            ALTER TABLE search_docket
            ALTER COLUMN {column} DROP NOT NULL,
            ALTER COLUMN {column} DROP DEFAULT;
        """)

    # Integer column that should be nullable
    op.execute("""
        ALTER TABLE search_docket
        ALTER COLUMN view_count DROP NOT NULL,
        ALTER COLUMN view_count DROP DEFAULT;
    """)

    print("✓ Made 20 columns nullable to match CSV data")
    print("  Columns can now accept NULL values from CSV import")


def downgrade() -> None:
    """Restore NOT NULL constraints (will fail if NULL data exists)."""

    # This downgrade will only work if there's no NULL data in the columns
    nullable_text_columns = [
        'cause', 'nature_of_suit', 'jury_demand', 'jurisdiction_type',
        'filepath_local', 'filepath_ia', 'filepath_ia_json',
        'assigned_to_str', 'referred_to_str', 'appeal_from_str', 'panel_str',
        'appellate_fee_status', 'appellate_case_type_information',
        'mdl_status', 'docket_number_core', 'federal_dn_case_type',
        'federal_dn_judge_initials_assigned', 'federal_dn_judge_initials_referred',
        'federal_dn_office_code', 'docket_number_raw'
    ]

    for column in nullable_text_columns:
        op.execute(f"""
            ALTER TABLE search_docket
            ALTER COLUMN {column} SET DEFAULT '',
            ALTER COLUMN {column} SET NOT NULL;
        """)

    op.execute("""
        ALTER TABLE search_docket
        ALTER COLUMN view_count SET DEFAULT 0,
        ALTER COLUMN view_count SET NOT NULL;
    """)

    print("✓ Restored NOT NULL constraints on 20 columns")
