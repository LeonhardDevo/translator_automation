"""merge heads

Revision ID: 1125a6b6d4b2
Revises: 11a735b1c0d1, 6f236b851676
Create Date: 2026-02-27 12:24:18.644927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1125a6b6d4b2'
down_revision: Union[str, Sequence[str], None] = ('11a735b1c0d1', '6f236b851676')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
