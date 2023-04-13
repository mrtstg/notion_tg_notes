import datetime
from aiogram import F, Router
from aiogram.filters.command import Command
from aiogram.types import Message
from api.api import NotionApi, NotionNote
from config import get_config
from api.properties import CheckboxPageProperty, DatePageProperty, SelectPageProperty

router = Router()
CONFIG = get_config()


@router.message(Command("week"))
async def get_next_week_notes(message: Message, api_client: NotionApi):
    notes = await api_client.query_notes(
        CONFIG.db_id,
        DatePageProperty("Date").next_week_filter,
        [
            DatePageProperty("Date").ascending_sort,
            SelectPageProperty("Importance").descending_sort,
        ],
    )
    text = "Заметки на следующую неделю:\n"
    if not notes.results:
        await message.answer("Нет заметок на следующую неделю!")
        return
    for note in notes.results:
        text += NotionNote.from_json(note).represent() + "\n"
    await message.answer(text)


@router.message(Command("today"))
async def get_today_notes(message: Message, api_client: NotionApi):
    now = datetime.datetime.now()
    now = datetime.datetime(now.year, now.month, now.day)
    tomorrow = datetime.datetime.fromtimestamp(now.timestamp() + 86399)

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
    text = "Заметки на сегодня:\n"
    if notes.results:
        for note in notes.results:
            text += NotionNote.from_json(note).represent() + "\n"
    else:
        text = "Заметок на сегодня больше нет!"
    await message.reply(text)
