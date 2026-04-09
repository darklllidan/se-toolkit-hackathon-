"""
Reminder functions called by APScheduler at the scheduled time.
These are NOT aiogram handlers — they are plain async functions.
"""
from aiogram import Bot

from app import api_client
from app.config import settings


async def send_reminder(booking_id: str, telegram_id: int) -> None:
    """Send a 5-minute reminder to the user before their booking starts."""
    booking = await api_client.get_booking(booking_id)
    if not booking or booking.get("status") != "confirmed":
        return  # Booking was cancelled, skip

    from datetime import datetime
    starts_at = datetime.fromisoformat(booking["starts_at"])

    bot = Bot(token=settings.bot_token)
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                f"⏰ <b>Напоминание!</b>\n\n"
                f"Через 5 минут начинается твоё бронирование:\n"
                f"🕐 {starts_at.strftime('%H:%M')} — ресурс {booking['resource_id'][:8]}...\n\n"
                f"Не забудь! 👋"
            ),
            parse_mode="HTML",
        )
    finally:
        await bot.session.close()

    await api_client.mark_reminder_sent(booking_id)
