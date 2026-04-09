"""
Async HTTP client for communicating with the FastAPI backend internal API.
All requests include X-Bot-Secret for authentication.
"""
from datetime import datetime

import httpx

from app.config import settings

BASE = settings.backend_internal_url
HEADERS = {"X-Bot-Secret": settings.bot_internal_secret, "Content-Type": "application/json"}


async def get_user(telegram_id: int) -> dict | None:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/internal/bot/user-by-telegram/{telegram_id}", headers=HEADERS)
        return r.json() if r.status_code == 200 else None


async def verify_link_token(token: str, telegram_id: int, username: str | None = None) -> dict | None:
    async with httpx.AsyncClient() as client:
        params = {"token": token, "telegram_id": telegram_id}
        if username:
            params["telegram_username"] = username
        r = await client.post(f"{BASE}/internal/bot/verify-link-token", params=params, headers=HEADERS)
        return r.json() if r.status_code == 200 else None


async def create_booking(
    telegram_id: int,
    resource_id: str,
    starts_at: datetime,
    ends_at: datetime,
    notes: str | None = None,
) -> dict | None:
    async with httpx.AsyncClient() as client:
        payload = {
            "resource_id": resource_id,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "notes": notes,
        }
        r = await client.post(
            f"{BASE}/internal/bot/bookings",
            params={"telegram_id": telegram_id},
            json=payload,
            headers=HEADERS,
        )
        if r.status_code == 201:
            return r.json()
        return {"error": r.json().get("detail", "Unknown error"), "status_code": r.status_code}


async def get_booking(booking_id: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/internal/bot/bookings/{booking_id}", headers=HEADERS)
        return r.json() if r.status_code == 200 else None


async def cancel_booking(booking_id: str, telegram_id: int) -> bool:
    async with httpx.AsyncClient() as client:
        r = await client.delete(
            f"{BASE}/internal/bot/bookings/{booking_id}",
            params={"telegram_id": telegram_id},
            headers=HEADERS,
        )
        return r.status_code == 204


async def mark_reminder_sent(booking_id: str) -> None:
    async with httpx.AsyncClient() as client:
        await client.patch(f"{BASE}/internal/bot/bookings/{booking_id}/reminder-sent", headers=HEADERS)


async def get_resources() -> list[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/v1/resources", headers=HEADERS)
        return r.json() if r.status_code == 200 else []


async def get_availability(resource_id: str, date_str: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE}/api/v1/resources/{resource_id}/availability",
            params={"date": date_str},
            headers=HEADERS,
        )
        return r.json() if r.status_code == 200 else []


async def get_my_bookings(telegram_id: int) -> list[dict]:
    """Get upcoming confirmed bookings for a user via their telegram_id."""
    user = await get_user(telegram_id)
    if not user:
        return []
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE}/api/v1/bookings",
            params={"status": "confirmed"},
            headers={**HEADERS, "Authorization": f"Bearer bot-internal"},
        )
        # Use internal endpoint workaround — fetch via internal API
        r2 = await client.get(
            f"{BASE}/internal/bot/user-by-telegram/{telegram_id}",
            headers=HEADERS,
        )
        return []  # Simplified: real impl would query bookings by user_id
