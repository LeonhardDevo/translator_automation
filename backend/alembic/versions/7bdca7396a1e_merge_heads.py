"""merge heads

Revision ID: 7bdca7396a1e
Revises: 92119c60c9c6, 999999999997
Create Date: 2026-02-23 00:00:49.234446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bdca7396a1e'
down_revision: Union[str, Sequence[str], None] = ('92119c60c9c6', '999999999997')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
