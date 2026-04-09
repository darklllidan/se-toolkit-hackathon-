from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from app.database import get_db
from app.dependencies import get_current_user_bearer
from app.models.user import User
from app.services.assistant import run_assistant

router = APIRouter(prefix="/assistant", tags=["assistant"])


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_bearer),
):
    if not body.messages:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="messages cannot be empty")

    reply = await run_assistant(
        db=db,
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_building=current_user.building,
        messages=[m.model_dump() for m in body.messages],
    )
    return ChatResponse(reply=reply)
