from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Записаться на ТО"), KeyboardButton(text="🤖 ИИ диагностика")],
        [KeyboardButton(text="🔍 Статус ремонта"), KeyboardButton(text="💰 Узнать стоимость ремонта")],
        [KeyboardButton(text="👨‍🔧 Связаться с деж. мастером"), KeyboardButton(text="📍 Адрес")]
    ],
    resize_keyboard=True
)
