from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import types

kb_choise_main_menu = [
    [types.KeyboardButton(text="Посмотреть информацию")],
    [types.KeyboardButton(text="Записаться на время")],
    [types.KeyboardButton(text="О Devman...")]
]
main_menu = types.ReplyKeyboardMarkup(
    keyboard=kb_choise_main_menu,
    resize_keyboard=True,)
