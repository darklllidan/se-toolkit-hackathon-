import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.handlers import availability, booking, cancel, start
from app.middlewares.auth import TelegramAuthMiddleware
from app.scheduler import scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware runs for every incoming update
    dp.update.middleware(TelegramAuthMiddleware())

    # Register all routers
    dp.include_router(start.router)
    dp.include_router(availability.router)
    dp.include_router(booking.router)
    dp.include_router(cancel.router)

    scheduler.start()
    logger.info("Scheduler started")

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
