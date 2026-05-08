"""create initial admin user

Revision ID: e93ce913eabd
Revises: f1f04095a338
Create Date: 2026-01-22 00:49:01.117248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e93ce913eabd'
down_revision: Union[str, Sequence[str], None] = 'f1f04095a338'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Import necessary modules
    from pwdlib import PasswordHash
    from pwdlib.hashers.argon2 import Argon2Hasher
    from datetime import datetime
    
    # Initialize pwdlib with Argon2 hasher (same as in security module)
    pwd = PasswordHash([Argon2Hasher()])
    
    # Get the connection
    conn = op.get_bind()
    
    # Hash the default admin password (we'll use "admin123" as default)
    admin_password_hash = pwd.hash("admin123")
    
    # Insert the initial admin user
    conn.execute(
        sa.text("""
            INSERT INTO admin (email, full_name, hashed_password, is_active, created_at)
            VALUES (:email, :full_name, :hashed_password, :is_active, :created_at)
        """),
        {
            'email': 'admin@translationsystem.com',
            'full_name': 'System Administrator',
            'hashed_password': admin_password_hash,
            'is_active': True,
            'created_at': datetime.utcnow()
        }
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the initial admin user
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM admin WHERE email = :email"),
        {'email': 'admin@translationsystem.com'}
    )

