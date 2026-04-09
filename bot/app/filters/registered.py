from aiogram.filters import BaseFilter
from aiogram.types import Message


class IsRegisteredFilter(BaseFilter):
    """Passes only if the user has linked their Telegram account."""

    async def __call__(self, message: Message, is_linked: bool = False) -> bool:
        return is_linked
