import uuid

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.auth import decode_token


async def get_current_user(
    token: str = Query(..., alias="token", include_in_schema=False),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Used by WebSocket endpoint (token in query param)."""
    return await _resolve_token(token, db)


async def get_current_user_bearer(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Used by regular HTTP endpoints (Authorization: Bearer <token>)."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")
    token = authorization[7:]
    return await _resolve_token(token, db)


async def _resolve_token(token: str, db: AsyncSession) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


async def get_current_admin(
    user: User = Depends(get_current_user_bearer),
) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


async def verify_bot_secret(x_bot_secret: str = Header(...)) -> None:
    if x_bot_secret != settings.bot_internal_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bot secret")
