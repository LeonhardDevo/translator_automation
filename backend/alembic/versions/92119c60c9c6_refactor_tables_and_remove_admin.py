"""refactor_tables_and_remove_admin

Revision ID: 92119c60c9c6
Revises: 9b06974a6e46
Create Date: 2026-02-17 10:24:58.375668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92119c60c9c6'
down_revision: Union[str, Sequence[str], None] = '9b06974a6e46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop admin table
    op.drop_table('admin')
    
    # Rename tables
    op.rename_table('user', 'users')
    op.rename_table('document', 'documents')


def downgrade() -> None:
    # Revert table renames
    op.rename_table('documents', 'document')
    op.rename_table('users', 'user')
    
    # Recreate admin table (minimal schema for restore)
    op.create_table('admin',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_admin_email', 'admin', ['email'], unique=True)
