from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from . import make_row_keyboard

router = Router()

available_importance = ["Важно", "Неважно", "Срочно"]
available_remind_values = ["Да", "Нет"]
available_progress = ["Не начато", "Начато", "Завершено"]
available_categories = ["Работа", "Дом", "Учеба", "Преподавательство"]


class NoteCreatingStage(StatesGroup):
    IMPORTANCE, REMIND, PROGESS, CATEGORIES, TITLE = [State() for _ in range(5)]


@router.message(Command("note"))
async def create_note(message: Message, state: FSMContext):
    await message.answer("Введите заголовок заметки: ")
    await state.set_state(NoteCreatingStage.TITLE)


@router.message(NoteCreatingStage.TITLE, F.text.len() > 0)
async def set_note_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        text="Выберите уровень важности:",
        reply_markup=make_row_keyboard(available_importance),
    )
    await state.set_state(NoteCreatingStage.IMPORTANCE)


@router.message(NoteCreatingStage.IMPORTANCE, F.text.in_(available_importance))
async def set_note_importance(message: Message, state: FSMContext):
    await state.update_data(importance=message.text)
    await message.answer(
        str(await state.get_data()), reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()
