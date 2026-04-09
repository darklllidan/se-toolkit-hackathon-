"""Add is_ta column and seed admin user

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-09
"""
import os
import uuid

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def _hash_password(plain: str) -> str:
    """Minimal bcrypt hash without importing app code."""
    import bcrypt  # available in container
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def upgrade() -> None:
    # Add is_ta column
    op.add_column("users", sa.Column("is_ta", sa.Boolean(), nullable=False, server_default="false"))

    # Seed admin user (idempotent)
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    hashed = _hash_password(admin_password)
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO users (id, email, hashed_password, full_name, building, room_number,
                           is_active, is_admin, is_ta)
        VALUES (
            gen_random_uuid(),
            'admin@campus.local',
            :hashed,
            'Admin',
            NULL,
            NULL,
            TRUE,
            TRUE,
            FALSE
        )
        ON CONFLICT (email) DO NOTHING
    """).bindparams(hashed=hashed))


def downgrade() -> None:
    op.execute("DELETE FROM users WHERE email = 'admin@campus.local'")
    op.drop_column("users", "is_ta")
