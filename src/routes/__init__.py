from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from numpy import array_split


def make_row_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    buttons = [KeyboardButton(text=item) for item in items]
    markup = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
    for row in array_split(buttons, 3):  # type: ignore
        markup.keyboard.append(list(row))

    return markup
