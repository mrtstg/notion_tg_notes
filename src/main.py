from datetime import datetime
from api.api import NotionApi, NotionNote
from api.properties import CheckboxPageProperty
from config import FileConfig
import asyncio
import os
from aiogram import Bot, Dispatcher
from routes import common, note_creating

CONFIG = FileConfig(os.environ.get("CONFIG_FILE", "config.yaml"))

loop = asyncio.new_event_loop()
api = NotionApi(CONFIG.token, loop)
asyncio.set_event_loop(loop)


async def main():
    dp = Dispatcher()
    bot = Bot(CONFIG.tg_token)

    dp.include_router(common.router)
    dp.include_router(note_creating.router)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    loop.run_until_complete(main())
