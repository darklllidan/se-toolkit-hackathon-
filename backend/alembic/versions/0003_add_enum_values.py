"""Add study_room and dryer to resource_category enum

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-09
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE resource_category ADD VALUE IF NOT EXISTS 'study_room'")
    op.execute("ALTER TYPE resource_category ADD VALUE IF NOT EXISTS 'dryer'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; downgrade is a no-op
    pass
