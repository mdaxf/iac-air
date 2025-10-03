"""Create uploaded files table

Revision ID: 016
Revises: 015
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create uploaded_files table
    op.create_table('uploaded_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('db_alias', sa.String(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),  # 'pdf', 'docx', 'xlsx', 'csv', 'txt', 'md'
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),  # Storage path
        sa.Column('mime_type', sa.String(), nullable=True),

        # Processing status
        sa.Column('status', sa.String(), server_default='uploaded', nullable=False),  # 'uploaded', 'processing', 'completed', 'failed'
        sa.Column('processing_progress', sa.Float(), server_default='0.0', nullable=True),  # 0.0 to 1.0
        sa.Column('error_message', sa.Text(), nullable=True),

        # Content metadata (JSONB)
        # {
        #   "title": "Database Schema Documentation",
        #   "author": "John Doe",
        #   "description": "Comprehensive guide to customer tables",
        #   "tags": ["schema", "customer", "orders"],
        #   "category": "documentation",
        #   "page_count": 50,
        #   "word_count": 15000
        # }
        sa.Column('content_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Processing results (JSONB)
        # {
        #   "chunks_created": 45,
        #   "embeddings_generated": 45,
        #   "tables_mentioned": ["customers", "orders"],
        #   "extraction_method": "pdf_plumber",
        #   "processing_time_ms": 5432
        # }
        sa.Column('processing_results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Audit fields
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('uploaded_by', sa.String(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_uploaded_files_db_alias', 'uploaded_files', ['db_alias'])
    op.create_index('ix_uploaded_files_file_name', 'uploaded_files', ['file_name'])
    op.create_index('ix_uploaded_files_file_type', 'uploaded_files', ['file_type'])
    op.create_index('ix_uploaded_files_status', 'uploaded_files', ['status'])
    op.create_index('ix_uploaded_files_uploaded_at', 'uploaded_files', ['uploaded_at'])
    op.create_index('ix_uploaded_files_uploaded_by', 'uploaded_files', ['uploaded_by'])


def downgrade() -> None:
    op.drop_index('ix_uploaded_files_uploaded_by', table_name='uploaded_files')
    op.drop_index('ix_uploaded_files_uploaded_at', table_name='uploaded_files')
    op.drop_index('ix_uploaded_files_status', table_name='uploaded_files')
    op.drop_index('ix_uploaded_files_file_type', table_name='uploaded_files')
    op.drop_index('ix_uploaded_files_file_name', table_name='uploaded_files')
    op.drop_index('ix_uploaded_files_db_alias', table_name='uploaded_files')
    op.drop_table('uploaded_files')
