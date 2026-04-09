import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    building: Mapped[int | None] = mapped_column(SmallInteger(), nullable=True)
    room_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    student_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_ta: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    bookings: Mapped[list["Booking"]] = relationship(  # noqa: F821
        "Booking", back_populates="user", cascade="all, delete-orphan"
    )
    link_tokens: Mapped[list["TelegramLinkToken"]] = relationship(
        "TelegramLinkToken", back_populates="user", cascade="all, delete-orphan"
    )


class TelegramLinkToken(Base):
    __tablename__ = "telegram_link_tokens"

    token: Mapped[str] = mapped_column(String(10), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="link_tokens")
