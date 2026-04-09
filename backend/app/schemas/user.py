import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator


class UserRegister(BaseModel):
    full_name: str
    building: int
    room_number: str
    password: str
    ta_code: str | None = None

    @field_validator("building")
    @classmethod
    def building_in_range(cls, v: int) -> int:
        if not 1 <= v <= 7:
            raise ValueError("Building must be between 1 and 7")
        return v

    @field_validator("full_name", "room_number")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_room_for_dorm(self) -> "UserRegister":
        room = self.room_number or ""
        dorm = self.building or 0
        if not room.isdigit() or len(room) not in (3, 4):
            raise ValueError("Room must be 3–4 digits (e.g. 204 or 1301)")
        floor = int(room[0]) if len(room) == 3 else int(room[:2])
        max_floor = 4 if dorm <= 4 else (5 if dorm == 5 else 13)
        if floor < 1 or floor > max_floor:
            raise ValueError(f"Dorm {dorm} has floors 1–{max_floor}")
        return self


class UserLoginRequest(BaseModel):
    full_name: str
    building: int
    room_number: str
    password: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    building: int | None
    room_number: str | None
    student_id: str | None
    telegram_id: int | None
    telegram_username: str | None
    is_active: bool
    is_admin: bool
    is_ta: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TelegramLinkCodeOut(BaseModel):
    code: str
    expires_in_seconds: int
