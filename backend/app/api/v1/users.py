from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user_bearer
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user_bearer)):
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user_bearer),
    db: AsyncSession = Depends(get_db),
):
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.student_id is not None:
        user.student_id = data.student_id
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/me", status_code=204)
async def deactivate_me(
    user: User = Depends(get_current_user_bearer),
    db: AsyncSession = Depends(get_db),
):
    user.is_active = False
    db.add(user)
    await db.commit()
