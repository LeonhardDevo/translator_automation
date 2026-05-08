"""add target_language to document table

Revision ID: 4e1d4a3b5c26
Revises: 34a7f5b4c0d1
Create Date: 2026-01-23 06:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '4e1d4a3b5c26'
down_revision: Union[str, Sequence[str], None] = '34a7f5b4c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the target_language column to the document table
    op.add_column('document', sa.Column('target_language', sa.String(), nullable=True))
    
    # Update existing records to have a default value
    op.execute("UPDATE document SET target_language = 'Turkmen' WHERE target_language IS NULL")


def downgrade() -> None:
    # Remove the target_language column from the document table
    op.drop_column('document', 'target_language')