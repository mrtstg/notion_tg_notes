from api.api import NotionApi
import time
from api.structs import NotionNote
from config import get_config
import asyncio
from aiogram import Bot
from logger import get_logger
import logging
import datetime

logger = get_logger(__name__, logging.INFO)
CONFIG = get_config()
loop = asyncio.new_event_loop()
api = NotionApi(CONFIG, loop)
asyncio.set_event_loop(loop)


async def send_message(bot: Bot, text: str):
    for tgid in CONFIG.tg_ids:
        await bot.send_message(tgid, text)


async def main():
    bot = Bot(CONFIG.tg_token)
    last_minute = datetime.datetime.fromtimestamp(time.time() - 60).minute
    while True:
        try:
            now_date = datetime.datetime.now()
            if now_date.minute == last_minute:
                await asyncio.sleep(5)
                continue
            last_minute = now_date.minute

            notes = await api.get_today_notes(CONFIG.db_id, True)
            timeflag = f't{now_date.strftime("%H:%M")}'
            if timeflag == "t07:00":
                await api.create_today_notes(CONFIG.db_id, CONFIG.daily_notes)

            filtered_notes: list[NotionNote] = list(
                filter(lambda x: timeflag in x.remind.variants, notes)
            )
            if not filtered_notes:
                continue
            text = "🔔Напоминание о незавершенных заметках:\n"
            for note in filtered_notes:
                text += note.represent() + "\n"
            await send_message(bot, text)
        except Exception as e:
            logger.error(str(e))
            await asyncio.sleep(15)


if __name__ == "__main__":
    logger.info("Скрипт проверок запущен!")
    loop.run_until_complete(main())
