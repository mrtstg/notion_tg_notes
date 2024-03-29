import datetime
from typing import Any, Callable, Match
from aiogram import F, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove
from api.api import NotionApi, NotionNote
from api.properties import DatePageProperty, TitlePageProperty
from .date_mapper import (
    AbstractDateMapper,
    ClosestWeekDayDateMapper,
    TodayDateMapper,
    TomorrowDateMapper,
)
from . import make_row_keyboard
from config import get_config
from logger import get_logger
import logging

logger = get_logger(__name__, logging.INFO)
router = Router()
CONFIG = get_config()

available_date_mappers: dict[str, AbstractDateMapper] = {
    "Сегодня": TodayDateMapper(),
    "Завтра": TomorrowDateMapper(),
    "Ближайший ПН": ClosestWeekDayDateMapper(0),
    "Ближайший ВТ": ClosestWeekDayDateMapper(1),
    "Ближайшая СР": ClosestWeekDayDateMapper(2),
    "Ближайший ЧТ": ClosestWeekDayDateMapper(3),
    "Ближайший ПТ": ClosestWeekDayDateMapper(4),
    "Ближайшая СБ": ClosestWeekDayDateMapper(5),
    "Ближайшее ВС": ClosestWeekDayDateMapper(6),
}
available_date_mappers_keys: list[str] = list(available_date_mappers.keys())


class NoteCreatingStage(StatesGroup):
    IMPORTANCE, REMIND, CATEGORIES, TITLE, DATE = [State() for _ in range(5)]


async def create_note_in_notion(message: Message, state: FSMContext, api: NotionApi):
    message_data: dict[Any, Any] = {
        "reply_markup": ReplyKeyboardRemove(),  # type: ignore
        "text": "Заметка создана!",
    }

    data = await state.get_data()
    note = NotionNote()
    note.date.begin_date = data["begin_date"]
    note.date.end_date = data["end_date"]
    note.category.variants = data["categories"]
    note.title.text = data["title"]
    note.importance.selected = data["importance"]
    note.progress.selected = data["progress"]
    note.remind.variants = data["remind"]
    logger.info("Создаю заметку %s" % note.title_value)

    try:
        await api.create_note(note, CONFIG.db_id)
    except Exception as e:
        logger.error("Не удалось создать заметку: %s" % e)
        message_data["text"] = "Ошибка при создании заметки!"

    await message.reply(**message_data)  # type: ignore
    await state.set_state(None)
    await state.set_data({})


@router.message(Command("daily"))
async def create_daily_notes(message: Message, api_client: NotionApi):
    await api_client.create_today_notes(CONFIG.db_id, CONFIG.daily_notes)
    await message.reply(f"Созданы недостающие заметки")


@router.message(Command("note"))
async def create_note(message: Message, state: FSMContext):
    await message.reply("Введите заголовок заметки: ")
    await state.update_data(categories=[], progress=CONFIG.progress_values[0])
    await state.set_state(NoteCreatingStage.TITLE)


@router.message(NoteCreatingStage.TITLE, F.text.len() > 0)
async def set_note_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.reply(
        text="Выберите уровень важности:",
        reply_markup=make_row_keyboard(CONFIG.importance_values),
    )
    await state.set_state(NoteCreatingStage.IMPORTANCE)


@router.message(NoteCreatingStage.IMPORTANCE, F.text.in_(CONFIG.importance_values))
async def set_note_importance(message: Message, state: FSMContext):
    await state.update_data(importance=message.text)
    await message.reply(
        text="Напомнить о наличии заметки?",
        reply_markup=make_row_keyboard(["Да", "Нет"]),
    )
    await state.set_state(NoteCreatingStage.REMIND)


@router.message(NoteCreatingStage.REMIND, F.text.in_(["Да", "Нет"]))
async def set_note_remind(message: Message, state: FSMContext):
    await state.update_data(
        remind=[] if message.text == "Нет" else CONFIG.default_remind_flags
    )
    await message.reply(
        text="Введите категории заметки.",
        reply_markup=make_row_keyboard(CONFIG.categories_values + ["done"]),
    )
    await state.set_state(NoteCreatingStage.CATEGORIES)


@router.message(NoteCreatingStage.CATEGORIES, F.text == "done")
async def end_note_creation(message: Message, state: FSMContext):
    await message.reply(
        text="Введите дату или диапазон дат, на которое нужно назначить заметку.",
        reply_markup=make_row_keyboard(available_date_mappers_keys),
    )
    await state.set_state(NoteCreatingStage.DATE)


@router.message(NoteCreatingStage.CATEGORIES, F.text.in_(CONFIG.categories_values))
async def note_category_action(message: Message, state: FSMContext):
    assert message.text is not None
    generate_categories: Callable[
        [list[str]], str
    ] = lambda x: "Текущие категории: " + ",".join(x)
    cat_list: list[str] = (await state.get_data())["categories"]
    if message.text in cat_list:
        cat_list.pop(cat_list.index(message.text))
        await message.reply(text="Категория удалена!\n" + generate_categories(cat_list))
    else:
        cat_list.append(message.text)
        await message.reply(
            text="Категория добавлена!\n" + generate_categories(cat_list)
        )


@router.message(NoteCreatingStage.DATE, F.text.in_(available_date_mappers_keys))
async def date_bindings_action(
    message: Message, state: FSMContext, api_client: NotionApi
):
    assert message.text is not None
    date_mapper = available_date_mappers[message.text]
    await state.update_data(
        begin_date=date_mapper.get_begin_date(), end_date=date_mapper.get_end_date()
    )
    await create_note_in_notion(message, state, api_client)


@router.message(
    NoteCreatingStage.DATE,
    F.text.regexp(r"^([0-9]{1,2})\.([0-9]{1,2})$").as_("date_match"),
)
async def custom_yearless_date_input_action(
    message: Message, state: FSMContext, date_match: Match[str], api_client: NotionApi
):
    try:
        await state.update_data(
            end_date=None,
            begin_date=datetime.datetime(
                datetime.datetime.now().year,
                int(date_match.group(2)),
                int(date_match.group(1)),
            ),
        )
    except Exception:
        await message.reply("Неправильная дата!")
    await create_note_in_notion(message, state, api_client)


@router.message(
    NoteCreatingStage.DATE,
    F.text.regexp(r"^([0-9]{1,2})\.([0-9]{1,2})-([0-9]{1,2})\.([0-9]{1,2})$").as_(
        "date_match"
    ),
)
async def custon_yearless_date_range_input_action(
    message: Message, state: FSMContext, date_match: Match[str], api_client: NotionApi
):
    now = datetime.datetime.now()
    try:
        await state.update_data(
            end_date=datetime.datetime(
                now.year, int(date_match.group(2)), int(date_match.group(1))
            ),
            begin_date=datetime.datetime(
                now.year, int(date_match.group(4)), int(date_match.group(3))
            ),
        )
    except Exception:
        await message.reply("Неправильная дата!")
    await create_note_in_notion(message, state, api_client)


@router.message(
    NoteCreatingStage.DATE,
    F.text.regexp(r"([0-9]{1,2}):([0-9]{1,2})").as_("date_match"),
)
async def custom_time_range_input_action(
    message: Message, state: FSMContext, date_match: Match[str], api_client: NotionApi
):
    now = datetime.datetime.now()
    try:
        now = datetime.datetime(
            now.year,
            now.month,
            now.day,
            int(date_match.group(1)),
            int(date_match.group(2)),
        )
        await state.update_data(end_date=None, begin_date=now)
    except:
        await message.reply("Неправильная дата!")
    await create_note_in_notion(message, state, api_client)
