"""Rename metadata to document_metadata in vector_documents_enhanced

Revision ID: 018
Revises: 017
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename metadata column to document_metadata to avoid SQLAlchemy reserved name conflict
    op.alter_column(
        'vector_documents_enhanced',
        'metadata',
        new_column_name='document_metadata',
        existing_type=sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True
    )


def downgrade() -> None:
    # Rename back to metadata
    op.alter_column(
        'vector_documents_enhanced',
        'document_metadata',
        new_column_name='metadata',
        existing_type=sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True
    )
