from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CATEGORIES = {
    "washing_machine": "🫧 Стиральная машина",
    "meeting_room": "📋 Переговорная",
    "rest_area": "🛋 Зона отдыха",
}

DURATIONS = [1, 2, 3, 4]


def categories_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"cat:{key}")]
        for key, label in CATEGORIES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def resources_keyboard(resources: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{r['name']} — {r['location']}",
            callback_data=f"res:{r['id']}"
        )]
        for r in resources
    ]
    buttons.append([InlineKeyboardButton(text="◀ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def date_keyboard() -> InlineKeyboardMarkup:
    from datetime import date, timedelta
    today = date.today()
    buttons = [
        [
            InlineKeyboardButton(text="Сегодня", callback_data=f"date:{today.isoformat()}"),
            InlineKeyboardButton(text="Завтра", callback_data=f"date:{(today + timedelta(days=1)).isoformat()}"),
        ],
        [InlineKeyboardButton(text="◀ Назад", callback_data="back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def time_slots_keyboard(slots: list[dict]) -> InlineKeyboardMarkup:
    from datetime import datetime
    buttons = []
    for slot in slots:
        if slot["is_available"]:
            start = datetime.fromisoformat(slot["starts_at"])
            label = f"✅ {start.strftime('%H:%M')}"
            buttons.append([InlineKeyboardButton(text=label, callback_data=f"time:{slot['starts_at']}")])
    buttons.append([InlineKeyboardButton(text="◀ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def duration_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"{h}ч", callback_data=f"dur:{h}") for h in DURATIONS]
    ]
    buttons.append([InlineKeyboardButton(text="◀ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking"),
        ]
    ])


def my_bookings_keyboard(bookings: list[dict]) -> InlineKeyboardMarkup:
    from datetime import datetime
    buttons = []
    for b in bookings:
        start = datetime.fromisoformat(b["starts_at"])
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {start.strftime('%d.%m %H:%M')} — {b['resource_id'][:8]}...",
                callback_data=f"cancel:{b['id']}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
