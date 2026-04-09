from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app import api_client

router = Router()

HELP_TEXT = """
<b>Campus Resource Sync Bot</b>

Доступные команды:
/start — Главное меню
/link &lt;код&gt; — Привязать аккаунт с сайта
/available — Доступные ресурсы прямо сейчас
/book — Забронировать ресурс
/mybookings — Мои бронирования
/cancel — Отменить бронирование
/help — Эта справка
"""


@router.message(CommandStart())
async def cmd_start(message: Message, is_linked: bool, user: dict | None):
    if is_linked:
        await message.answer(
            f"Привет, {user['full_name']}! Используй /book чтобы забронировать ресурс."
        )
    else:
        await message.answer(
            "Привет! Я бот Campus Resource Sync.\n\n"
            "Чтобы начать, войди на сайт и привяжи Telegram-аккаунт:\n"
            "1. Получи код на сайте (кнопка «Привязать Telegram»)\n"
            "2. Отправь мне: /link ABCD12"
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode="HTML")


@router.message(Command("link"))
async def cmd_link(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Укажи код: /link ABCD12")
        return

    code = parts[1].upper()
    user = message.from_user
    result = await api_client.verify_link_token(
        token=code,
        telegram_id=user.id,
        username=user.username,
    )
    if result and result.get("ok"):
        await message.answer(
            f"Аккаунт успешно привязан! Привет, {result['full_name']} 👋\n"
            "Теперь можешь использовать /book для бронирования."
        )
    else:
        await message.answer("Неверный или истёкший код. Получи новый на сайте.")
