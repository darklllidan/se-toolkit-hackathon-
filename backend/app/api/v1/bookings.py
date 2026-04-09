import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user_bearer
from datetime import date as date_type

from app.models.booking import Booking, BookingStatus
from app.models.resource import Resource
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingOut, BookingTimelineItem
from app.services.booking import cancel_booking, create_booking

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/timeline", response_model=list[BookingTimelineItem])
async def get_timeline(
    date: str = Query(..., description="YYYY-MM-DD"),
    user: User = Depends(get_current_user_bearer),
    db: AsyncSession = Depends(get_db),
):
    day = date_type.fromisoformat(date)
    tz = timezone.utc
    day_start = datetime(day.year, day.month, day.day, 0, 0, tzinfo=tz)
    day_end   = datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=tz)

    from sqlalchemy.orm import aliased
    UserAlias = aliased(User)
    result = await db.execute(
        select(Booking, Resource.name, UserAlias.full_name)
        .join(Resource, Booking.resource_id == Resource.id)
        .join(UserAlias, Booking.user_id == UserAlias.id)
        .where(
            Booking.status == BookingStatus.confirmed,
            Booking.starts_at >= day_start,
            Booking.starts_at <= day_end,
        )
    )
    rows = result.all()
    return [
        BookingTimelineItem(
            id=b.id,
            resource_id=b.resource_id,
            resource_name=resource_name,
            starts_at=b.starts_at,
            ends_at=b.ends_at,
            is_mine=(b.user_id == user.id),
            user_name=full_name,
        )
        for b, resource_name, full_name in rows
    ]


@router.get("/admin/all", response_model=list[dict])
async def list_all_bookings(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin only: all confirmed bookings with resource and user info."""
    from sqlalchemy.orm import aliased
    UserAlias = aliased(User)
    result = await db.execute(
        select(Booking, Resource.name, UserAlias.full_name)
        .join(Resource, Booking.resource_id == Resource.id)
        .join(UserAlias, Booking.user_id == UserAlias.id)
        .where(Booking.status == BookingStatus.confirmed)
        .order_by(Booking.starts_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": str(b.id),
            "resource_id": str(b.resource_id),
            "resource_name": rname,
            "user_name": uname,
            "starts_at": b.starts_at.isoformat(),
            "ends_at": b.ends_at.isoformat(),
            "status": b.status.value,
        }
        for b, rname, uname in rows
    ]


@router.get("", response_model=list[BookingOut])
async def list_bookings(
    booking_status: BookingStatus | None = Query(None, alias="status"),
    from_dt: datetime | None = Query(None, alias="from"),
    to_dt: datetime | None = Query(None, alias="to"),
    user: User = Depends(get_current_user_bearer),
    db: AsyncSession = Depends(get_db),
):
    query = select(Booking).where(Booking.user_id == user.id)
    if booking_status:
        query = query.where(Booking.status == booking_status)
    if from_dt:
        query = query.where(Booking.starts_at >= from_dt)
    if to_dt:
        query = query.where(Booking.ends_at <= to_dt)
    query = query.order_by(Booking.starts_at)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def make_booking(
    data: BookingCreate,
    user: User = Depends(get_current_user_bearer),
    db: AsyncSession = Depends(get_db),
):
    # Enforce max 3h for students (TAs and admins are exempt)
    duration = data.ends_at - data.starts_at
    if not (user.is_ta or user.is_admin) and duration > timedelta(hours=3):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Students can book for a maximum of 3 hours",
        )

    try:
        booking = await create_booking(
            db,
            user_id=user.id,
            resource_id=data.resource_id,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            notes=data.notes,
            user_name=user.full_name,
        )
    except ValueError as e:
        code = 404 if "not found" in str(e).lower() else 409
        raise HTTPException(status_code=code, detail=str(e))
    return booking


@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(
    booking_id: uuid.UUID,
    user: User = Depends(get_current_user_bearer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    return booking


@router.delete("/{booking_id}", status_code=204)
async def cancel_booking_route(
    booking_id: uuid.UUID,
    user: User = Depends(get_current_user_bearer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    if booking.status != BookingStatus.confirmed:
        raise HTTPException(status_code=409, detail="Only confirmed bookings can be cancelled")
    await cancel_booking(db, booking)
