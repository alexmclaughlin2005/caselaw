"""Add search indexes for dockets and opinions

Revision ID: 62a6263eb9a0
Revises: cf47bd255dfb
Create Date: 2025-11-12 16:02:47.375653

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '62a6263eb9a0'
down_revision = 'cf47bd255dfb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add GIN indexes for full-text search on dockets
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_docket_case_name_gin
        ON search_docket USING GIN(to_tsvector('english', coalesce(case_name, '')))
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_docket_case_name_short_gin
        ON search_docket USING GIN(to_tsvector('english', coalesce(case_name_short, '')))
    """)

    # Add composite indexes for common queries on dockets
    op.create_index(
        'idx_docket_court_date',
        'search_docket',
        ['court_id', 'date_filed'],
        postgresql_using='btree'
    )

    op.create_index(
        'idx_docket_assigned_to',
        'search_docket',
        ['assigned_to_id'],
        postgresql_where=sa.text('assigned_to_id IS NOT NULL'),
        postgresql_using='btree'
    )

    # Add GIN indexes for full-text search on opinions
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_opinion_case_name_gin
        ON search_opinioncluster USING GIN(to_tsvector('english', coalesce(case_name, '')))
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_opinion_judges_gin
        ON search_opinioncluster USING GIN(to_tsvector('english', coalesce(judges, '')))
    """)

    # Add composite indexes for common queries on opinions
    op.create_index(
        'idx_opinion_date_citation',
        'search_opinioncluster',
        ['date_filed', 'citation_count'],
        postgresql_using='btree'
    )

    # Add indexes for citation queries
    op.create_index(
        'idx_citation_citing_cited',
        'search_opinionscited',
        ['citing_opinion_id', 'cited_opinion_id'],
        postgresql_using='btree'
    )

    op.create_index(
        'idx_citation_cited_citing',
        'search_opinionscited',
        ['cited_opinion_id', 'citing_opinion_id'],
        postgresql_using='btree'
    )


def downgrade() -> None:
    # Drop GIN indexes
    op.execute("DROP INDEX IF EXISTS idx_docket_case_name_gin")
    op.execute("DROP INDEX IF EXISTS idx_docket_case_name_short_gin")
    op.execute("DROP INDEX IF EXISTS idx_opinion_case_name_gin")
    op.execute("DROP INDEX IF EXISTS idx_opinion_judges_gin")

    # Drop composite indexes
    op.drop_index('idx_docket_court_date', table_name='search_docket')
    op.drop_index('idx_docket_assigned_to', table_name='search_docket')
    op.drop_index('idx_opinion_date_citation', table_name='search_opinioncluster')
    op.drop_index('idx_citation_citing_cited', table_name='search_opinionscited')
    op.drop_index('idx_citation_cited_citing', table_name='search_opinionscited')

