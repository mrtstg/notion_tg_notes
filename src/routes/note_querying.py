import datetime
from aiogram import F, Router
from aiogram.filters.command import Command
from aiogram.types import Message
from api.api import NotionApi, NotionNote
from config import get_config
from api.properties import CheckboxPageProperty, DatePageProperty, SelectPageProperty
import logging
from logger import get_logger
from routes.date_mapper import TodayDateMapper, TomorrowDateMapper

logger = get_logger(__name__, logging.INFO)
router = Router()
CONFIG = get_config()


@router.message(Command("week"))
async def get_next_week_notes(message: Message, api_client: NotionApi):
    logger.info("Получаю заметки на неделю.")
    notes = await api_client.query_notes(
        CONFIG.db_id,
        DatePageProperty("Date").next_week_filter,
        [
            DatePageProperty("Date").ascending_sort,
            SelectPageProperty("Importance").descending_sort,
        ],
    )
    logger.info("Заметки на неделю получены!")
    text = "Заметки на следующую неделю:\n"
    if not notes.results:
        await message.reply("Нет заметок на следующую неделю!")
        return
    for note in notes.results:
        text += NotionNote.from_json(note).represent() + "\n"
    await message.reply(text)


@router.message(Command("tomorrow"))
async def get_tomorrow_notes(message: Message, api_client: NotionApi):
    tomorrow_begin = TomorrowDateMapper().get_begin_date()
    tomorrow_end = datetime.datetime.fromtimestamp(tomorrow_begin.timestamp() + 86399)
    logger.info("Получаю заметки на завтра")
    notes = await api_client.query_notes(
        CONFIG.db_id,
        {
            "and": [
                DatePageProperty(
                    "Date", "Europe/Moscow", tomorrow_begin
                ).on_or_after_filter,
                DatePageProperty(
                    "Date", "Europe/Moscow", tomorrow_end
                ).on_or_before_filter,
                SelectPageProperty("Progress", "Завершено").not_equals_filter,
            ]
        },
    )
    logger.info("Заметки на завтра получены")
    if not notes.results:
        await message.reply("Заметок на завтра нет!")
        return
    text = "Заметки на завтра:\n"
    for note in notes.results:
        text += NotionNote.from_json(note).represent() + "\n"
    await message.reply(text)


@router.message(Command("today"))
async def get_today_notes(message: Message, api_client: NotionApi):
    now = TodayDateMapper().get_begin_date()
    tomorrow = datetime.datetime.fromtimestamp(now.timestamp() + 86399)

    logger.info("Получаю заметки на сегодня")
    notes = await api_client.query_notes(
        CONFIG.db_id,
        {
            "and": [
                DatePageProperty("Date", "Europe/Moscow", now).on_or_after_filter,
                DatePageProperty("Date", "Europe/Moscow", tomorrow).on_or_before_filter,
                SelectPageProperty("Progress", "Завершено").not_equals_filter,
            ]
        },
        [DatePageProperty("Date").ascending_sort],
    )
    logger.info("Заметки на сегодня получены")
    text = "Заметки на сегодня:\n"
    if notes.results:
        for note in notes.results:
            text += NotionNote.from_json(note).represent() + "\n"
    else:
        text = "Заметок на сегодня больше нет!"
    await message.reply(text)
