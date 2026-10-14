from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import main_kb
from bot.keyboards.location import location_kb, LATITUDE, LONGITUDE

router = Router()

@router.message(F.text == "🔙 Отмена / Главное меню")
@router.message(Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    await message.answer("Действие отменено. Вы вернулись в главное меню:", reply_markup=main_kb)

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}!\n"
        "Добро пожаловать в автосервис <b>Восток</b>. Выберите нужный раздел меню:",
        reply_markup=main_kb
    )

@router.message(F.text == "📍 Адрес")
async def show_address(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Отправляем карточку, где в поле адреса помещены адрес, график и телефон
    await message.answer_venue(
        latitude=LATITUDE,
        longitude=LONGITUDE,
        title="Автосервис «Восток»",
        address="г. Санкт-Петербург, Невский пр., д. 1\n📞 Тел: +7 (812) 000-00-00\n⏰ 09:00 - 21:00 (без вых.)",
        reply_markup=location_kb
    )

@router.message(F.text == "👨‍🔧 Связаться с деж. мастером")
async def call_master(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👨‍🔧 <b>Дежурный мастер на связи:</b>\n"
        "Telegram: @master_service\n"
        "Прямой телефон: +7 (812) 111-22-33",
        reply_markup=main_kb
    )

@router.message(F.text == "💰 Узнать стоимость ремонта")
async def get_price(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "💰 <b>Ориентировочный прайс-лист:</b>\n\n"
        "• Компьютерная диагностика — от 1 500 ₽\n"
        "• Замена масла и фильтра — от 1 200 ₽\n"
        "• Замена передних колодок — от 1 800 ₽\n"
        "• Регламентное ТО — от 4 500 ₽\n\n"
        "<i>Точная стоимость зависит от марки и модели автомобиля.</i>",
        reply_markup=main_kb
    )
