from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔙 Отмена / Главное меню")]
    ],
    resize_keyboard=True
)
