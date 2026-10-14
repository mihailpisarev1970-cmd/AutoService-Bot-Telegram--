from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.services.ai_service import analyze_car_issue
from bot.keyboards.cancel import cancel_kb
from bot.keyboards.main_menu import main_kb

router = Router()

class DiagStates(StatesGroup):
    waiting_for_description = State()

@router.message(F.text == "🤖 ИИ диагностика")
async def start_ai_diag(message: types.Message, state: FSMContext):
    await state.set_state(DiagStates.waiting_for_description)
    await message.answer(
        "🛠 <b>Режим умной автодиагностики</b>\n\n"
        "Опишите своими словами, что происходит с авто:\n"
        "• <b>Обязательно укажите марку, модель и год выпуска авто</b>\n"
        "• Что беспокоит (стук, вибрация, скрип, свист)?\n"
        "• При каких условиях проявляется (на холодную, на скорости, при торможении)?\n\n"
        "<i>Или нажмите кнопку отмены внизу, чтобы вернуться в меню:</i>",
        reply_markup=cancel_kb
    )

@router.message(DiagStates.waiting_for_description)
async def process_ai_diag(message: types.Message, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    status_msg = await message.answer("⏳ Мастер-диагност изучает описание...")

    result = await analyze_car_issue(message.text)

    await status_msg.delete()
    await message.answer(result, reply_markup=main_kb)
    await state.clear()
