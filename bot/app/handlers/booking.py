"""
Booking FSM handler.
Flow: category → resource → date → start time → duration → confirm
"""
import re
from datetime import date, datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app import api_client
from app.filters.registered import IsRegisteredFilter
from app.keyboards.inline import (
    CATEGORIES,
    categories_keyboard,
    confirm_keyboard,
    date_keyboard,
    duration_keyboard,
    resources_keyboard,
    time_slots_keyboard,
)
from app.scheduler import add_reminder_job
from app.states.booking import BookingFSM

router = Router()

# Regex patterns for natural language input
_NATURAL_PATTERNS = [
    re.compile(
        r"(?:забронируй?|book)\s+(?P<category>стиралк[уи]|meeting room|переговорк[уи]|зону?\s+отдыха|washing machine)"
        r".*?(?:на\s+|at\s+)(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?",
        re.IGNORECASE,
    )
]

_NATURAL_CATEGORY_MAP = {
    "стиралк": "washing_machine",
    "washing machine": "washing_machine",
    "переговорк": "meeting_room",
    "meeting room": "meeting_room",
    "зон": "rest_area",
    "rest area": "rest_area",
}


def _parse_natural(text: str) -> dict | None:
    for pattern in _NATURAL_PATTERNS:
        m = pattern.search(text)
        if m:
            cat_raw = m.group("category").lower()
            category = next((v for k, v in _NATURAL_CATEGORY_MAP.items() if k in cat_raw), None)
            if not category:
                return None
            hour = int(m.group("hour"))
            minute = int(m.group("minute") or 0)
            return {"category": category, "hour": hour, "minute": minute}
    return None


@router.message(Command("book"), IsRegisteredFilter())
async def cmd_book(message: Message, state: FSMContext):
    # Try natural language parse first
    parsed = _parse_natural(message.text or "")
    if parsed:
        await state.update_data(
            category=parsed["category"],
            prefilled_hour=parsed["hour"],
            prefilled_minute=parsed["minute"],
            prefilled_date=date.today().isoformat(),
        )
        resources = await api_client.get_resources()
        filtered = [r for r in resources if r["category"] == parsed["category"] and r["status"] == "available"]
        if not filtered:
            await message.answer("Нет доступных ресурсов в этой категории.")
            return
        await state.set_state(BookingFSM.choosing_resource)
        await message.answer("Выбери ресурс:", reply_markup=resources_keyboard(filtered))
    else:
        await state.set_state(BookingFSM.choosing_category)
        await message.answer("Что хочешь забронировать?", reply_markup=categories_keyboard())


@router.message(Command("book"))
async def cmd_book_unlinked(message: Message):
    await message.answer("Сначала привяжи аккаунт: /link ABCD12")


# ── Step 1: Category selected ─────────────────────────────────────────────────

@router.callback_query(BookingFSM.choosing_category, F.data.startswith("cat:"))
async def on_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[1]
    await state.update_data(category=category)

    resources = await api_client.get_resources()
    filtered = [r for r in resources if r["category"] == category and r["status"] == "available"]
    if not filtered:
        await callback.message.edit_text("Нет доступных ресурсов в этой категории.")
        await state.clear()
        return

    await state.set_state(BookingFSM.choosing_resource)
    await callback.message.edit_text("Выбери ресурс:", reply_markup=resources_keyboard(filtered))


# ── Step 2: Resource selected ─────────────────────────────────────────────────

@router.callback_query(BookingFSM.choosing_resource, F.data.startswith("res:"))
async def on_resource(callback: CallbackQuery, state: FSMContext):
    resource_id = callback.data.split(":")[1]
    await state.update_data(resource_id=resource_id)

    data = await state.get_data()
    if data.get("prefilled_date"):
        # Skip date step, go straight to time selection
        slots = await api_client.get_availability(resource_id, data["prefilled_date"])
        available = [s for s in slots if s["is_available"]]
        if not available:
            await callback.message.edit_text("На сегодня нет свободных слотов.")
            await state.clear()
            return
        await state.update_data(chosen_date=data["prefilled_date"], slots=slots)
        await state.set_state(BookingFSM.choosing_duration)
        # If hour was prefilled, skip time step too
        prefilled_hour = data.get("prefilled_hour")
        if prefilled_hour is not None:
            chosen_slot = next(
                (s for s in available if datetime.fromisoformat(s["starts_at"]).hour == prefilled_hour),
                None,
            )
            if chosen_slot:
                await state.update_data(starts_at=chosen_slot["starts_at"])
                await state.set_state(BookingFSM.choosing_duration)
                await callback.message.edit_text("На сколько часов?", reply_markup=duration_keyboard())
                return
        await state.set_state(BookingFSM.choosing_start_time)
        await callback.message.edit_text("Выбери время начала:", reply_markup=time_slots_keyboard(available))
    else:
        await state.set_state(BookingFSM.choosing_date)
        await callback.message.edit_text("Выбери дату:", reply_markup=date_keyboard())


# ── Step 3: Date selected ─────────────────────────────────────────────────────

@router.callback_query(BookingFSM.choosing_date, F.data.startswith("date:"))
async def on_date(callback: CallbackQuery, state: FSMContext):
    chosen_date = callback.data.split(":")[1]
    data = await state.get_data()
    slots = await api_client.get_availability(data["resource_id"], chosen_date)
    available = [s for s in slots if s["is_available"]]
    if not available:
        await callback.message.edit_text("На эту дату нет свободных слотов. Выбери другую дату.")
        return

    await state.update_data(chosen_date=chosen_date, slots=slots)
    await state.set_state(BookingFSM.choosing_start_time)
    await callback.message.edit_text("Выбери время начала:", reply_markup=time_slots_keyboard(available))


# ── Step 4: Start time selected ───────────────────────────────────────────────

@router.callback_query(BookingFSM.choosing_start_time, F.data.startswith("time:"))
async def on_time(callback: CallbackQuery, state: FSMContext):
    starts_at = callback.data.split(":", 1)[1]
    await state.update_data(starts_at=starts_at)
    await state.set_state(BookingFSM.choosing_duration)
    await callback.message.edit_text("На сколько часов?", reply_markup=duration_keyboard())


# ── Step 5: Duration selected ─────────────────────────────────────────────────

@router.callback_query(BookingFSM.choosing_duration, F.data.startswith("dur:"))
async def on_duration(callback: CallbackQuery, state: FSMContext):
    hours = int(callback.data.split(":")[1])
    data = await state.get_data()
    starts_at = datetime.fromisoformat(data["starts_at"])
    ends_at = starts_at + timedelta(hours=hours)

    await state.update_data(ends_at=ends_at.isoformat(), duration_hours=hours)

    # Build confirmation summary
    resource_id = data["resource_id"]
    resources = await api_client.get_resources()
    resource = next((r for r in resources if r["id"] == resource_id), None)
    resource_name = resource["name"] if resource else resource_id
    cat_label = CATEGORIES.get(data.get("category", ""), "")

    summary = (
        f"<b>Подтверди бронирование:</b>\n\n"
        f"📍 Ресурс: {resource_name}\n"
        f"🗂 Категория: {cat_label}\n"
        f"📅 Дата: {data['chosen_date']}\n"
        f"⏰ Время: {starts_at.strftime('%H:%M')} — {ends_at.strftime('%H:%M')} ({hours}ч)\n"
    )
    await state.update_data(summary=summary)
    await state.set_state(BookingFSM.confirming)
    await callback.message.edit_text(summary, parse_mode="HTML", reply_markup=confirm_keyboard())


# ── Step 6: Confirm ───────────────────────────────────────────────────────────

@router.callback_query(BookingFSM.confirming, F.data == "confirm")
async def on_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    telegram_id = callback.from_user.id
    result = await api_client.create_booking(
        telegram_id=telegram_id,
        resource_id=data["resource_id"],
        starts_at=datetime.fromisoformat(data["starts_at"]),
        ends_at=datetime.fromisoformat(data["ends_at"]),
    )

    if result and "error" not in result:
        starts_at = datetime.fromisoformat(result["starts_at"])
        reminder_time = starts_at - timedelta(minutes=5)
        if reminder_time > datetime.now(timezone.utc):
            add_reminder_job(result["id"], telegram_id, reminder_time)

        await callback.message.edit_text(
            f"✅ Бронирование подтверждено!\n"
            f"ID: <code>{result['id'][:8]}...</code>\n"
            f"Напомню за 5 минут до начала.",
            parse_mode="HTML",
        )
    else:
        error = result.get("error", "Неизвестная ошибка") if result else "Ошибка сети"
        await callback.message.edit_text(f"❌ Не удалось забронировать: {error}")


# ── Cancel during FSM ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "cancel_booking")
async def on_cancel_fsm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Бронирование отменено.")


@router.callback_query(F.data == "back")
async def on_back(callback: CallbackQuery, state: FSMContext):
    current = await state.get_state()
    if current == BookingFSM.choosing_resource:
        await state.set_state(BookingFSM.choosing_category)
        await callback.message.edit_text("Что хочешь забронировать?", reply_markup=categories_keyboard())
    elif current == BookingFSM.choosing_date:
        data = await state.get_data()
        resources = await api_client.get_resources()
        filtered = [r for r in resources if r["category"] == data.get("category") and r["status"] == "available"]
        await state.set_state(BookingFSM.choosing_resource)
        await callback.message.edit_text("Выбери ресурс:", reply_markup=resources_keyboard(filtered))
    else:
        await state.clear()
        await callback.message.edit_text("Отменено. Начни сначала с /book")
