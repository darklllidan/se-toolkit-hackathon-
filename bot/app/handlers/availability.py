from datetime import date, datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app import api_client
from app.filters.registered import IsRegisteredFilter
from app.keyboards.inline import CATEGORIES

router = Router()


@router.message(Command("available"), IsRegisteredFilter())
async def cmd_available(message: Message):
    resources = await api_client.get_resources()
    if not resources:
        await message.answer("Ресурсы не найдены.")
        return

    today = date.today().isoformat()
    now = datetime.now(timezone.utc)
    lines = ["<b>Доступность прямо сейчас:</b>\n"]

    for resource in resources:
        if resource["status"] != "available":
            continue
        slots = await api_client.get_availability(resource["id"], today)
        current_slot = next(
            (s for s in slots if s["is_available"] and
             datetime.fromisoformat(s["starts_at"]) <= now < datetime.fromisoformat(s["ends_at"])),
            None,
        )
        status = "✅ Свободно" if current_slot else "🔴 Занято"
        cat_label = CATEGORIES.get(resource["category"], resource["category"])
        lines.append(f"{cat_label} — <b>{resource['name']}</b> ({resource['location']}): {status}")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("available"))
async def cmd_available_unlinked(message: Message):
    await message.answer("Сначала привяжи аккаунт: /link ABCD12")
