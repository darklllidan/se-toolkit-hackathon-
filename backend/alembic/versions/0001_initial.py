"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable btree_gist extension for EXCLUDE constraint on time ranges
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # --- ENUMS (idempotent: skip if type already exists) ---
    conn = op.get_bind()
    existing = {r[0] for r in conn.execute(sa.text(
        "SELECT typname FROM pg_type WHERE typname IN ('resource_category','resource_status','booking_status')"
    ))}
    if "resource_category" not in existing:
        op.execute(sa.text("CREATE TYPE resource_category AS ENUM ('washing_machine', 'meeting_room', 'rest_area')"))
    if "resource_status" not in existing:
        op.execute(sa.text("CREATE TYPE resource_status AS ENUM ('available', 'maintenance', 'retired')"))
    if "booking_status" not in existing:
        op.execute(sa.text("CREATE TYPE booking_status AS ENUM ('confirmed', 'cancelled', 'completed', 'no_show')"))

    # --- USERS ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.Text, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("student_id", sa.String(50), nullable=True, unique=True),
        sa.Column("telegram_id", sa.BigInteger, nullable=True, unique=True),
        sa.Column("telegram_username", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_users_telegram_id", "users", ["telegram_id"],
                    postgresql_where=sa.text("telegram_id IS NOT NULL"))

    # --- RESOURCES ---
    op.create_table(
        "resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", postgresql.ENUM("washing_machine", "meeting_room", "rest_area", name="resource_category", create_type=False), nullable=False),
        sa.Column("location", sa.String(255), nullable=False),
        sa.Column("capacity", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("status", postgresql.ENUM("available", "maintenance", "retired", name="resource_status", create_type=False), nullable=False, server_default=sa.text("'available'")),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_resources_category", "resources", ["category"])
    op.create_index("idx_resources_status", "resources", ["status"])

    # --- BOOKINGS ---
    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", postgresql.ENUM("confirmed", "cancelled", "completed", "no_show", name="booking_status", create_type=False), nullable=False, server_default=sa.text("'confirmed'")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("reminder_sent", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("ends_at > starts_at", name="chk_booking_time_order"),
        sa.CheckConstraint("ends_at - starts_at <= INTERVAL '4 hours'", name="chk_booking_max_duration"),
    )

    # Partial indexes on bookings
    op.create_index("idx_bookings_resource_time", "bookings", ["resource_id", "starts_at", "ends_at"],
                    postgresql_where=sa.text("status = 'confirmed'"))
    op.create_index("idx_bookings_user_upcoming", "bookings", ["user_id", "starts_at"],
                    postgresql_where=sa.text("status = 'confirmed'"))
    op.create_index("idx_bookings_reminder", "bookings", ["starts_at", "reminder_sent"],
                    postgresql_where=sa.text("status = 'confirmed' AND reminder_sent = FALSE"))

    # THE KEY CONSTRAINT: prevent overlapping bookings for the same resource
    op.execute("""
        ALTER TABLE bookings
        ADD CONSTRAINT exc_no_overlapping_bookings
        EXCLUDE USING GIST (
            resource_id WITH =,
            tstzrange(starts_at, ends_at, '[)') WITH &&
        )
        WHERE (status = 'confirmed')
    """)

    # --- TELEGRAM LINK TOKENS ---
    op.create_table(
        "telegram_link_tokens",
        sa.Column("token", sa.String(10), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("telegram_link_tokens")
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS exc_no_overlapping_bookings")
    op.drop_table("bookings")
    op.drop_table("resources")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS booking_status")
    op.execute("DROP TYPE IF EXISTS resource_status")
    op.execute("DROP TYPE IF EXISTS resource_category")
