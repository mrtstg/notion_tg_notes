from typing import Generator
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def divide_chunks(lst: list, n: int) -> Generator[list[list], None, None]:
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def make_row_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    buttons = [KeyboardButton(text=item) for item in items]
    markup = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
    for row in divide_chunks(buttons, 4):
        markup.keyboard.append(list(row))  # type: ignore

    return markup
