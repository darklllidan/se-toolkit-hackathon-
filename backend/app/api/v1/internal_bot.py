"""
Internal bot API routes — only accessible on the Docker internal network.
Nginx blocks all /internal/* requests from the public internet.
Authentication is via X-Bot-Secret header.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_bot_secret
from app.models.booking import Booking, BookingStatus
from app.models.user import TelegramLinkToken, User
from app.schemas.booking import BookingCreate, BookingOut
from app.schemas.user import UserOut
from app.services.booking import cancel_booking, create_booking

router = APIRouter(
    prefix="/internal/bot",
    tags=["internal-bot"],
    dependencies=[Depends(verify_bot_secret)],
)


@router.post("/verify-link-token")
async def verify_link_token(
    token: str,
    telegram_id: int,
    telegram_username: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TelegramLinkToken).where(TelegramLinkToken.token == token)
    )
    link = result.scalar_one_or_none()
    if not link or link.used or link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == link.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.telegram_id = telegram_id
    if telegram_username:
        user.telegram_username = telegram_username
    link.used = True
    db.add(user)
    db.add(link)
    await db.commit()
    return {"ok": True, "user_id": str(user.id), "full_name": user.full_name}


@router.get("/user-by-telegram/{telegram_id}", response_model=UserOut)
async def get_user_by_telegram(
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not linked")
    return user


@router.post("/bookings", response_model=BookingOut, status_code=201)
async def bot_create_booking(
    telegram_id: int,
    data: BookingCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not linked")
    try:
        booking = await create_booking(
            db,
            user_id=user.id,
            resource_id=data.resource_id,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            notes=data.notes,
        )
    except ValueError as e:
        code = 404 if "not found" in str(e).lower() else 409
        raise HTTPException(status_code=code, detail=str(e))
    return booking


@router.get("/bookings/{booking_id}", response_model=BookingOut)
async def bot_get_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.delete("/bookings/{booking_id}", status_code=204)
async def bot_cancel_booking(
    booking_id: uuid.UUID,
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Verify ownership via telegram_id
    result = await db.execute(select(User).where(User.id == booking.user_id))
    user = result.scalar_one_or_none()
    if not user or user.telegram_id != telegram_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if booking.status != BookingStatus.confirmed:
        raise HTTPException(status_code=409, detail="Only confirmed bookings can be cancelled")
    await cancel_booking(db, booking)


@router.patch("/bookings/{booking_id}/reminder-sent", status_code=204)
async def mark_reminder_sent(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.reminder_sent = True
    db.add(booking)
    await db.commit()


@router.get("/upcoming-reminders", response_model=list[BookingOut])
async def get_upcoming_reminders(db: AsyncSession = Depends(get_db)):
    """Bookings starting in the next 5–10 minutes that haven't been reminded yet."""
    now = datetime.now(timezone.utc)
    window_start = now + timedelta(minutes=4, seconds=30)
    window_end = now + timedelta(minutes=10, seconds=30)
    result = await db.execute(
        select(Booking).where(
            Booking.status == BookingStatus.confirmed,
            Booking.reminder_sent == False,  # noqa: E712
            Booking.starts_at >= window_start,
            Booking.starts_at <= window_end,
        )
    )
    return result.scalars().all()
