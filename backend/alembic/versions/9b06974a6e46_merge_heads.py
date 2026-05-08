"""merge_heads

Revision ID: 9b06974a6e46
Revises: 4e1d4a3b5c26, 999999999998
Create Date: 2026-02-17 10:20:52.183221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b06974a6e46'
down_revision: Union[str, Sequence[str], None] = ('4e1d4a3b5c26', '999999999998')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
