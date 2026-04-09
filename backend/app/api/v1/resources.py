import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user_bearer
from app.models.booking import Booking, BookingStatus
from app.models.resource import Resource, ResourceStatus
from app.models.user import User
from app.schemas.resource import ResourceCreate, ResourceOut, ResourceUpdate, SlotOut

router = APIRouter(prefix="/resources", tags=["resources"])

SLOT_DURATION_HOURS = 1


@router.get("", response_model=list[ResourceOut])
async def list_resources(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user_bearer),
):
    result = await db.execute(
        select(Resource).where(Resource.status != ResourceStatus.retired).order_by(Resource.category, Resource.name)
    )
    return result.scalars().all()


@router.get("/{resource_id}", response_model=ResourceOut)
async def get_resource(
    resource_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user_bearer),
):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.get("/{resource_id}/availability", response_model=list[SlotOut])
async def get_availability(
    resource_id: uuid.UUID,
    date_param: date = Query(..., alias="date"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user_bearer),
):
    """Returns 1-hour slots for the full 24 hours with availability for the given date."""
    tz = timezone.utc
    day_start = datetime(date_param.year, date_param.month, date_param.day, 0, 0, tzinfo=tz)
    day_end = datetime(date_param.year, date_param.month, date_param.day, 23, 0, tzinfo=tz)

    # Fetch all confirmed bookings for this resource on this day
    result = await db.execute(
        select(Booking).where(
            Booking.resource_id == resource_id,
            Booking.status == BookingStatus.confirmed,
            Booking.starts_at >= day_start,
            Booking.ends_at <= day_end + timedelta(hours=SLOT_DURATION_HOURS),
        )
    )
    bookings = result.scalars().all()

    slots: list[SlotOut] = []
    current = day_start
    while current + timedelta(hours=SLOT_DURATION_HOURS) <= day_end + timedelta(hours=SLOT_DURATION_HOURS):
        slot_end = current + timedelta(hours=SLOT_DURATION_HOURS)
        is_booked = any(
            b.starts_at < slot_end and b.ends_at > current for b in bookings
        )
        slots.append(SlotOut(starts_at=current, ends_at=slot_end, is_available=not is_booked))
        current = slot_end

    return slots


@router.post("", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def create_resource(
    data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    resource = Resource(
        name=data.name,
        category=data.category,
        location=data.location,
        capacity=data.capacity,
        metadata_=data.metadata_,
    )
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource


@router.patch("/{resource_id}", response_model=ResourceOut)
async def update_resource(
    resource_id: uuid.UUID,
    data: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(resource, field, value)
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource


@router.delete("/{resource_id}", status_code=204)
async def retire_resource(
    resource_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    resource.status = ResourceStatus.retired
    db.add(resource)
    await db.commit()
