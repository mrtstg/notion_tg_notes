from typing import Callable
from aiogram import F, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove
from .date_mapper import (
    AbstractDateMapper,
    ClosestWeekDayDateMapper,
    TomorrowDateMapper,
)
from . import make_row_keyboard
from config import get_config

router = Router()
CONFIG = get_config()

available_date_mappers: dict[str, AbstractDateMapper] = {
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
    IMPORTANCE, REMIND, PROGESS, CATEGORIES, TITLE, DATE = [State() for _ in range(6)]


@router.message(Command("note"))
async def create_note(message: Message, state: FSMContext):
    await message.answer("Введите заголовок заметки: ")
    await state.update_data(categories=[])
    await state.set_state(NoteCreatingStage.TITLE)


@router.message(NoteCreatingStage.TITLE, F.text.len() > 0)
async def set_note_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        text="Выберите уровень важности:",
        reply_markup=make_row_keyboard(CONFIG.importance_values),
    )
    await state.set_state(NoteCreatingStage.IMPORTANCE)


@router.message(NoteCreatingStage.IMPORTANCE, F.text.in_(CONFIG.importance_values))
async def set_note_importance(message: Message, state: FSMContext):
    await state.update_data(importance=message.text)
    await message.answer(
        text="Выберите начальный прогресс заметки:",
        reply_markup=make_row_keyboard(CONFIG.progress_values),
    )
    await state.set_state(NoteCreatingStage.PROGESS)


@router.message(NoteCreatingStage.PROGESS, F.text.in_(CONFIG.progress_values))
async def set_note_progress(message: Message, state: FSMContext):
    await state.update_data(progress=message.text)
    await message.answer(
        text="Напомнить о наличии заметки?",
        reply_markup=make_row_keyboard(["Да", "Нет"]),
    )
    await state.set_state(NoteCreatingStage.REMIND)


@router.message(NoteCreatingStage.REMIND, F.text.in_(["Да", "Нет"]))
async def set_note_remind(message: Message, state: FSMContext):
    await state.update_data(remind=message.text == "Да")
    await message.answer(
        text="Введите категории заметки.",
        reply_markup=make_row_keyboard(CONFIG.categories_values + ["done"]),
    )
    await state.set_state(NoteCreatingStage.CATEGORIES)


@router.message(NoteCreatingStage.CATEGORIES, F.text == "done")
async def end_note_creation(message: Message, state: FSMContext):
    await message.answer(
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
        await message.answer(
            text="Категория удалена!\n" + generate_categories(cat_list)
        )
    else:
        cat_list.append(message.text)
        await message.answer(
            text="Категория добавлена!\n" + generate_categories(cat_list)
        )


@router.message(NoteCreatingStage.DATE, F.text.in_(available_date_mappers_keys))
async def date_bindings_action(message: Message, state: FSMContext):
    assert message.text is not None
    date_mapper = available_date_mappers[message.text]
    await state.update_data(
        begin_date=date_mapper.get_begin_date(), end_date=date_mapper.get_end_date()
    )
    await message.answer(
        str(await state.get_data()), reply_markup=ReplyKeyboardRemove()  # type: ignore
    )
    await state.set_state(None)
