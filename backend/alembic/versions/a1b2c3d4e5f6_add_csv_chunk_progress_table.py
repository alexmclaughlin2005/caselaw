"""add csv chunk progress table

Revision ID: a1b2c3d4e5f6
Revises: e3ed3d3cc887
Create Date: 2025-11-13 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'e3ed3d3cc887'
branch_labels = None
depends_on = None


def upgrade():
    # Create csv_chunk_progress table
    op.create_table(
        'csv_chunk_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('dataset_date', sa.String(length=20), nullable=False),
        sa.Column('chunk_number', sa.Integer(), nullable=False),
        sa.Column('chunk_filename', sa.String(length=255), nullable=False),
        sa.Column('chunk_start_row', sa.BigInteger(), nullable=True),
        sa.Column('chunk_end_row', sa.BigInteger(), nullable=True),
        sa.Column('chunk_row_count', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('rows_imported', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('rows_skipped', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('import_method', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('ix_csv_chunk_progress_table_name', 'csv_chunk_progress', ['table_name'])
    op.create_index('ix_csv_chunk_progress_dataset_date', 'csv_chunk_progress', ['dataset_date'])
    op.create_index('ix_csv_chunk_progress_chunk_number', 'csv_chunk_progress', ['chunk_number'])
    op.create_index('ix_csv_chunk_progress_status', 'csv_chunk_progress', ['status'])

    # Create composite index for common query pattern
    op.create_index(
        'ix_csv_chunk_progress_table_date',
        'csv_chunk_progress',
        ['table_name', 'dataset_date']
    )


def downgrade():
    # Drop indexes
    op.drop_index('ix_csv_chunk_progress_table_date', table_name='csv_chunk_progress')
    op.drop_index('ix_csv_chunk_progress_status', table_name='csv_chunk_progress')
    op.drop_index('ix_csv_chunk_progress_chunk_number', table_name='csv_chunk_progress')
    op.drop_index('ix_csv_chunk_progress_dataset_date', table_name='csv_chunk_progress')
    op.drop_index('ix_csv_chunk_progress_table_name', table_name='csv_chunk_progress')

    # Drop table
    op.drop_table('csv_chunk_progress')
