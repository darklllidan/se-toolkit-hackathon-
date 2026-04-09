from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app import api_client


class TelegramAuthMiddleware(BaseMiddleware):
    """
    Resolves telegram_id → linked user profile for every incoming update.
    Injects `user` (dict or None) and `is_linked` (bool) into handler data.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from_user = getattr(event, "from_user", None) or getattr(
            getattr(event, "message", None), "from_user", None
        )
        if from_user:
            user = await api_client.get_user(from_user.id)
            data["user"] = user
            data["is_linked"] = user is not None
        else:
            data["user"] = None
            data["is_linked"] = False
        return await handler(event, data)
