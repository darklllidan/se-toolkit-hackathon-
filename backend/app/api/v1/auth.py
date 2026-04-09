import random
import string
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user_bearer
from app.models.user import TelegramLinkToken, User
from app.schemas.token import Token
from app.schemas.user import (
    AdminLoginRequest,
    TelegramLinkCodeOut,
    UserLoginRequest,
    UserOut,
    UserRegister,
)
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _synthetic_email(full_name: str, building: int, room_number: str) -> str:
    slug = full_name.lower().replace(" ", "_")
    return f"b{building}r{room_number}_{slug}@campus.local"


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(
            func.lower(User.full_name) == data.full_name.lower(),
            User.building == data.building,
            User.room_number == data.room_number,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A user with this name and room already exists")

    is_ta = bool(data.ta_code and data.ta_code.strip() == settings.ta_registration_code)

    email = _synthetic_email(data.full_name, data.building, data.room_number)
    user = User(
        email=email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        building=data.building,
        room_number=data.room_number,
        is_ta=is_ta,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A user with this name and room already exists")
    await db.refresh(user)
    return user


@router.post("/token", response_model=Token)
async def login(data: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(
            func.lower(User.full_name) == data.full_name.strip().lower(),
            User.building == data.building,
            User.room_number == data.room_number.strip(),
        )
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return Token(
        access_token=create_access_token(str(user.id), user.is_admin),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/admin/token", response_model=Token)
async def admin_login(data: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    """Separate login endpoint for admin portal — username + password only, no dorm/room."""
    result = await db.execute(
        select(User).where(
            func.lower(User.full_name) == data.username.strip().lower(),
            User.is_admin == True,  # noqa: E712
        )
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return Token(
        access_token=create_access_token(str(user.id), user.is_admin),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh: str, db: AsyncSession = Depends(get_db)):
    payload = decode_token(refresh)
    if payload.get("type") != "refresh" or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return Token(
        access_token=create_access_token(str(user.id), user.is_admin),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/link-telegram", response_model=TelegramLinkCodeOut)
async def generate_link_code(
    user: User = Depends(get_current_user_bearer),
    db: AsyncSession = Depends(get_db),
):
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    token = TelegramLinkToken(token=code, user_id=user.id, expires_at=expires_at)
    db.add(token)
    await db.commit()
    return TelegramLinkCodeOut(code=code, expires_in_seconds=600)
