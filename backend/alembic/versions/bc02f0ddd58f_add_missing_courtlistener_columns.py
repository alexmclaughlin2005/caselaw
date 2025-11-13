"""add_missing_courtlistener_columns

Revision ID: bc02f0ddd58f
Revises: 92dbfcfed916
Create Date: 2025-11-11 21:03:37.438896

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc02f0ddd58f'
down_revision = '92dbfcfed916'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add 32 missing columns from CourtListener official schema to search_docket table."""

    # Timestamp columns
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS date_created timestamp with time zone DEFAULT NOW() NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS date_modified timestamp with time zone DEFAULT NOW() NOT NULL;
    """)

    # Case details
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS cause character varying(2000) DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS nature_of_suit character varying(1000) DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS jury_demand character varying(500) DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS jurisdiction_type character varying(100) DEFAULT '' NOT NULL;
    """)

    # File paths
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS filepath_local character varying(1000) DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS filepath_ia character varying(1000) DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS filepath_ia_json character varying(1000) DEFAULT '' NOT NULL;
    """)

    # String representations
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS assigned_to_str text DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS referred_to_str text DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS appeal_from_str text DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS panel_str text DEFAULT '' NOT NULL;
    """)

    # Appellate information
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS appellate_fee_status text DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS appellate_case_type_information text DEFAULT '' NOT NULL;
    """)

    # MDL and view tracking
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS mdl_status character varying(100) DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS view_count integer DEFAULT 0 NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS date_last_index timestamp with time zone;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS date_last_filing date;
    """)

    # Internet Archive
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS ia_needs_upload boolean;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS ia_upload_failure_count smallint;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS ia_date_first_change timestamp with time zone;
    """)

    # Federal docket numbers (CRITICAL - this is where "mont", "mied", "njd" go!)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS docket_number_core character varying(20) DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS federal_dn_case_type character varying(6) DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS federal_dn_judge_initials_assigned character varying(5) DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS federal_dn_judge_initials_referred character varying(5) DEFAULT '' NOT NULL;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS federal_dn_office_code character varying(3) DEFAULT '' NOT NULL;
    """)

    # Additional fields
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS federal_defendant_number smallint;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS parent_docket_id integer;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS originating_court_information_id integer;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS idb_data_id integer;
    """)
    op.execute("""
        ALTER TABLE search_docket
        ADD COLUMN IF NOT EXISTS docket_number_raw character varying DEFAULT '' NOT NULL;
    """)

    print("✓ Added 32 missing columns to search_docket table")
    print("  Existing records will have default values for new columns")
    print("  New imports will populate all 52 columns properly")


def downgrade() -> None:
    """Remove the 32 columns added in upgrade (for rollback)."""

    # Drop all columns in reverse order
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS docket_number_raw;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS idb_data_id;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS originating_court_information_id;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS parent_docket_id;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS federal_defendant_number;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS federal_dn_office_code;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS federal_dn_judge_initials_referred;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS federal_dn_judge_initials_assigned;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS federal_dn_case_type;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS docket_number_core;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS ia_date_first_change;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS ia_upload_failure_count;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS ia_needs_upload;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS date_last_filing;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS date_last_index;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS view_count;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS mdl_status;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS appellate_case_type_information;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS appellate_fee_status;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS panel_str;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS appeal_from_str;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS referred_to_str;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS assigned_to_str;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS filepath_ia_json;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS filepath_ia;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS filepath_local;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS jurisdiction_type;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS jury_demand;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS nature_of_suit;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS cause;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS date_modified;")
    op.execute("ALTER TABLE search_docket DROP COLUMN IF EXISTS date_created;")

    print("✓ Removed 32 columns from search_docket table (rollback complete)")

