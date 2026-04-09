"""Add building and room_number to users

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("building", sa.SmallInteger(), nullable=True))
    op.add_column("users", sa.Column("room_number", sa.String(20), nullable=True))
    op.execute("""
        CREATE UNIQUE INDEX idx_users_name_building_room
        ON users (lower(full_name), building, room_number)
        WHERE building IS NOT NULL AND room_number IS NOT NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_users_name_building_room")
    op.drop_column("users", "room_number")
    op.drop_column("users", "building")
