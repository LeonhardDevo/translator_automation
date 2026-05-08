"""update subscription end dates to 10 years

Revision ID: 999999999997
Revises: 9b06974a6e46
Create Date: 2026-02-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '999999999997'
down_revision = '9b06974a6e46'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update all existing active subscriptions: set end_date = start_date + 10 years
    op.execute("""
        UPDATE user_subscriptions
        SET end_date = start_date + INTERVAL '3650 days'
        WHERE status = 'active'
    """)


def downgrade() -> None:
    # Revert to 30 days from start_date
    op.execute("""
        UPDATE user_subscriptions
        SET end_date = start_date + INTERVAL '30 days'
        WHERE status = 'active'
    """)
