from api.api import NotionApi
from config import get_config
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message
from routes import common, note_creating, note_querying
from logger import get_logger
import logging

logger = get_logger(__name__, logging.INFO)
CONFIG = get_config()
CONFIG.validate_daily_notes()

loop = asyncio.new_event_loop()
api = NotionApi(CONFIG, loop)
asyncio.set_event_loop(loop)


class ACLMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        if event.from_user is None or event.from_user.id not in CONFIG.tg_ids:
            return
        return await handler(event, data)


class ApiClientPassMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        data["api_client"] = api
        return await handler(event, data)


async def main():
    dp = Dispatcher()
    dp.message.middleware(ACLMiddleware())
    bot = Bot(CONFIG.tg_token)

    note_creating.router.message.middleware(ApiClientPassMiddleware())
    note_querying.router.message.middleware(ApiClientPassMiddleware())
    dp.include_router(common.router)
    dp.include_router(note_querying.router)
    dp.include_router(note_creating.router)

    logger.info("Бот начал работу!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logger.info("Скрипт запущен!")
    loop.run_until_complete(main())
