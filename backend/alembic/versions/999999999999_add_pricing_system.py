"""Add pricing system tables and update user table

Revision ID: 999999999999
Revises: f1f04095a338
Create Date: 2026-02-06 09:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from datetime import datetime

# revision identifiers
revision = '999999999999'
down_revision = 'f1f04095a338'
branch_labels = None
depends_on = None


def upgrade():
    # Create pricing plans table
    op.create_table('pricing_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('max_translations_per_month', sa.Integer(), nullable=False),
        sa.Column('price_per_month', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create usage records table
    op.create_table('usage_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('translation_count', sa.Integer(), nullable=False, default=0),
        sa.Column('reset_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create user subscriptions table
    op.create_table('user_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('pricing_plan_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default="active"),
        sa.Column('start_date', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['pricing_plan_id'], ['pricing_plans.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add role column to user table with a default value but allow NULL initially
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('role', sa.String(), nullable=True, default='user'))
    
    # Update existing users to have 'user' role
    conn = op.get_bind()
    conn.execute(text("UPDATE \"user\" SET role = 'user' WHERE role IS NULL OR role = ''"))
    
    # Now enforce NOT NULL constraint
    op.alter_column('user', 'role', nullable=False)

    # Create indexes
    op.create_index(op.f('ix_usage_records_user_id'), 'usage_records', ['user_id'])
    op.create_index(op.f('ix_user_subscriptions_user_id'), 'user_subscriptions', ['user_id'])
    op.create_index(op.f('ix_user_subscriptions_pricing_plan_id'), 'user_subscriptions', ['pricing_plan_id'])


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_user_subscriptions_pricing_plan_id'), table_name='user_subscriptions')
    op.drop_index(op.f('ix_user_subscriptions_user_id'), table_name='user_subscriptions')
    op.drop_index(op.f('ix_usage_records_user_id'), table_name='usage_records')

    # Drop tables in reverse order
    op.drop_table('user_subscriptions')
    op.drop_table('usage_records')
    op.drop_table('pricing_plans')

    # Remove role column from user table
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('role')