import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Text,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class BookingStatus(str, enum.Enum):
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="chk_booking_time_order"),
        CheckConstraint(
            "ends_at - starts_at <= INTERVAL '4 hours'",
            name="chk_booking_max_duration",
        ),
        # The EXCLUDE USING GIST constraint is defined in the Alembic migration
        # because SQLAlchemy doesn't natively support EXCLUDE constraints.
        # The migration creates:
        #   EXCLUDE USING GIST (
        #       resource_id WITH =,
        #       tstzrange(starts_at, ends_at, '[)') WITH &&
        #   ) WHERE (status = 'confirmed')
        Index(
            "idx_bookings_resource_time",
            "resource_id",
            "starts_at",
            "ends_at",
            postgresql_where="status = 'confirmed'",
        ),
        Index(
            "idx_bookings_user_upcoming",
            "user_id",
            "starts_at",
            postgresql_where="status = 'confirmed'",
        ),
        Index(
            "idx_bookings_reminder",
            "starts_at",
            "reminder_sent",
            postgresql_where="status = 'confirmed' AND reminder_sent = FALSE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        nullable=False,
        default=BookingStatus.confirmed,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship("User", back_populates="bookings")  # noqa: F821
    resource: Mapped["Resource"] = relationship("Resource", back_populates="bookings")
