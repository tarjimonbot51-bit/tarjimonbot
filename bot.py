from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import ErrorEvent

from config import Settings, load_settings
from database import Database
from handlers import admin, history, language, start, translate
from services.translator import TranslatorService

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    settings: Settings = load_settings()
    logger.info("Configuration loaded")
    database = Database(settings.database_path)
    await database.initialize()
    logger.info("Database initialized")

    translator = TranslatorService(settings.translation_api_url, settings.translation_api_key, settings.api_timeout)
    await translator.start()
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()

    @dispatcher.error()
    async def global_error_handler(event: ErrorEvent) -> bool:
        if isinstance(event.exception, TelegramNetworkError):
            logger.warning("Telegram network temporarily unavailable; update will not crash the bot: %s", event.exception)
            return True

        logger.exception("Unhandled update error", exc_info=event.exception)
        if event.update.message:
            try:
                await event.update.message.answer("⚠️ Kutilmagan xatolik yuz berdi.\n\nIltimos, birozdan keyin qayta urinib ko‘ring.")
            except TelegramNetworkError:
                logger.warning("Could not notify user because Telegram network is unavailable")
            except Exception:
                logger.exception("Could not notify user about error")
        return True

    dispatcher.include_router(start.create_router(database, settings))
    dispatcher.include_router(language.create_router(database))
    dispatcher.include_router(translate.create_router(database, translator))
    dispatcher.include_router(history.create_router(database))
    dispatcher.include_router(admin.create_router(database, settings))
    logger.info("Routers loaded")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot started")
        logger.info("Polling started")
        await dispatcher.start_polling(bot)
    finally:
        await translator.close()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (ValueError, RuntimeError) as exc:
        logger.error("Startup failed: %s", exc)
        sys.exit(1)
