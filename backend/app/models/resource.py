import enum
import uuid

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ResourceCategory(str, enum.Enum):
    washing_machine = "washing_machine"
    meeting_room = "meeting_room"
    rest_area = "rest_area"
    study_room = "study_room"
    dryer = "dryer"


class ResourceStatus(str, enum.Enum):
    available = "available"
    maintenance = "maintenance"
    retired = "retired"


class Resource(TimestampMixin, Base):
    __tablename__ = "resources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[ResourceCategory] = mapped_column(
        Enum(ResourceCategory, name="resource_category"), nullable=False
    )
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[ResourceStatus] = mapped_column(
        Enum(ResourceStatus, name="resource_status"),
        nullable=False,
        default=ResourceStatus.available,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    bookings: Mapped[list["Booking"]] = relationship(  # noqa: F821
        "Booking", back_populates="resource", cascade="all, delete-orphan"
    )
