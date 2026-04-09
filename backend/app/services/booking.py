import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.resource import Resource
from app.services.ws_manager import manager


async def create_booking(
    db: AsyncSession,
    user_id: uuid.UUID,
    resource_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    notes: str | None = None,
    user_name: str = "",
) -> Booking:
    """
    Creates a booking with conflict protection:
    1. SELECT FOR UPDATE serializes concurrent requests on the same resource.
    2. The PostgreSQL EXCLUDE USING GIST constraint catches any time overlap.
    Raises ValueError on conflict.
    """
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id).with_for_update()
    )
    resource = result.scalar_one_or_none()
    if resource is None:
        raise ValueError("Resource not found")

    booking = Booking(
        user_id=user_id,
        resource_id=resource_id,
        starts_at=starts_at,
        ends_at=ends_at,
        notes=notes,
    )
    db.add(booking)
    try:
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("Time slot is already booked for this resource")

    # Broadcast update to all connected dashboard clients
    await manager.broadcast(
        {
            "event": "booking_created",
            "booking_id": str(booking.id),
            "resource_id": str(resource_id),
            "resource_name": resource.name,
            "user_name": user_name,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "status": "confirmed",
        }
    )
    return booking


async def cancel_booking(
    db: AsyncSession,
    booking: Booking,
) -> Booking:
    booking.status = BookingStatus.cancelled
    db.add(booking)
    await db.commit()

    await manager.broadcast(
        {
            "event": "booking_cancelled",
            "booking_id": str(booking.id),
            "resource_id": str(booking.resource_id),
        }
    )
    return booking
