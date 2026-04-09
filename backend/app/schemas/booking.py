import uuid
from datetime import datetime

from pydantic import BaseModel, model_validator

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    resource_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    notes: str | None = None

    @model_validator(mode="after")
    def check_time_order(self) -> "BookingCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class BookingTimelineItem(BaseModel):
    id: uuid.UUID
    resource_id: uuid.UUID
    resource_name: str
    starts_at: datetime
    ends_at: datetime
    is_mine: bool
    user_name: str

    model_config = {"from_attributes": True}


class BookingOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resource_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    status: BookingStatus
    notes: str | None
    reminder_sent: bool
    created_at: datetime

    model_config = {"from_attributes": True}
