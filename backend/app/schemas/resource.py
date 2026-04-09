import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.resource import ResourceCategory, ResourceStatus


class ResourceCreate(BaseModel):
    name: str
    category: ResourceCategory
    location: str
    capacity: int = 1
    metadata_: dict | None = None


class ResourceUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    capacity: int | None = None
    status: ResourceStatus | None = None
    metadata_: dict | None = None


class ResourceOut(BaseModel):
    id: uuid.UUID
    name: str
    category: ResourceCategory
    location: str
    capacity: int
    status: ResourceStatus
    metadata_: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SlotOut(BaseModel):
    starts_at: datetime
    ends_at: datetime
    is_available: bool
