from api.api import NotionApi, NotionNote
import datetime
from api.properties import (
    DatePageProperty,
    MultiSelectPageProperty,
    SelectPageProperty,
    TitlePageProperty,
)
from config import get_config
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message
from routes import common, note_creating, note_querying

CONFIG = get_config()

loop = asyncio.new_event_loop()
api = NotionApi(CONFIG.token, loop)
asyncio.set_event_loop(loop)


class ApiClientPassMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        data["api_client"] = api
        return await handler(event, data)


async def main():
    dp = Dispatcher()
    bot = Bot(CONFIG.tg_token)

    note_creating.router.message.middleware(ApiClientPassMiddleware())
    note_querying.router.message.middleware(ApiClientPassMiddleware())
    dp.include_router(common.router)
    dp.include_router(note_querying.router)
    dp.include_router(note_creating.router)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    loop.run_until_complete(main())
