"""Update pricing plan fields to use count-based terminology

Revision ID: 999999999998
Revises: 999999999999
Create Date: 2026-02-06 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from datetime import datetime

# revision identifiers
revision = '999999999998'
down_revision = '999999999999'
branch_labels = None
depends_on = None


def upgrade():
    # Add the new columns
    op.add_column('pricing_plans', sa.Column('max_translation_count', sa.Integer(), nullable=True))
    op.add_column('pricing_plans', sa.Column('price_for_max_translation_per_counts', sa.Integer(), nullable=True))
    op.add_column('pricing_plans', sa.Column('description', sa.String(), nullable=True))
    
    # Copy data from old columns to new columns
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE pricing_plans 
        SET max_translation_count = max_translations_per_month,
            price_for_max_translation_per_counts = price_per_month,
            description = CASE 
                WHEN name = 'Free Trial' THEN '1-day free trial with limited translations'
                WHEN name = 'Basic' THEN 'Basic plan with standard translation allowance'
                WHEN name = 'Professional' THEN 'Professional plan with higher translation limits'
                WHEN name = 'Enterprise' THEN 'Enterprise plan with highest translation limits'
                ELSE name || ' plan'
            END
    """))
    
    # Make new columns non-nullable
    op.alter_column('pricing_plans', 'max_translation_count', nullable=False)
    op.alter_column('pricing_plans', 'price_for_max_translation_per_counts', nullable=False)
    op.alter_column('pricing_plans', 'description', nullable=False)
    
    # Drop the old columns
    op.drop_column('pricing_plans', 'max_translations_per_month')
    op.drop_column('pricing_plans', 'price_per_month')


def downgrade():
    # Add back the old columns
    op.add_column('pricing_plans', sa.Column('max_translations_per_month', sa.Integer(), nullable=True))
    op.add_column('pricing_plans', sa.Column('price_per_month', sa.Integer(), nullable=True))
    
    # Copy data from new columns back to old columns
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE pricing_plans 
        SET max_translations_per_month = max_translation_count,
            price_per_month = price_for_max_translation_per_counts
    """))
    
    # Make old columns non-nullable
    op.alter_column('pricing_plans', 'max_translations_per_month', nullable=False)
    op.alter_column('pricing_plans', 'price_per_month', nullable=False)
    
    # Drop the new columns and description
    op.drop_column('pricing_plans', 'max_translation_count')
    op.drop_column('pricing_plans', 'price_for_max_translation_per_counts')
    op.drop_column('pricing_plans', 'description')