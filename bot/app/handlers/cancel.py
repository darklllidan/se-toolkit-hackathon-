from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app import api_client
from app.filters.registered import IsRegisteredFilter
from app.scheduler import remove_reminder_job

router = Router()


@router.message(Command("cancel"), IsRegisteredFilter())
async def cmd_cancel(message: Message):
    telegram_id = message.from_user.id
    bookings = await api_client.get_my_bookings(telegram_id)

    if not bookings:
        await message.answer("У тебя нет активных бронирований.")
        return

    from datetime import datetime
    buttons = []
    for b in bookings:
        start = datetime.fromisoformat(b["starts_at"])
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {start.strftime('%d.%m %H:%M')} — {b.get('resource_name', b['resource_id'][:8])}",
                callback_data=f"cancel:{b['id']}",
            )
        ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выбери бронирование для отмены:", reply_markup=keyboard)


@router.message(Command("cancel"))
async def cmd_cancel_unlinked(message: Message):
    await message.answer("Сначала привяжи аккаунт: /link ABCD12")


@router.callback_query(F.data.startswith("cancel:"))
async def on_cancel_booking(callback: CallbackQuery):
    booking_id = callback.data.split(":")[1]
    telegram_id = callback.from_user.id

    success = await api_client.cancel_booking(booking_id, telegram_id)
    if success:
        remove_reminder_job(booking_id)
        await callback.message.edit_text("✅ Бронирование отменено.")
    else:
        await callback.message.edit_text("❌ Не удалось отменить. Возможно, бронирование уже неактивно.")
