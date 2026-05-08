"""add_theme_field_to_users_table

Revision ID: 11a735b1c0d2
Revises: 11a735b1c0d1
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '11a735b1c0d2'
down_revision = '11a735b1c0d1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('theme', sa.String(length=10), nullable=True, server_default='dark')
    )


def downgrade() -> None:
    op.drop_column('users', 'theme')
