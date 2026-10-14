
import os
import io
import aiohttp
import asyncio
import base64
from datetime import datetime, date, time, timedelta
import calendar
from PIL import Image

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext

from config import settings
import baserow_client
from states import BookingStates, AIDiagnosticStates

router = Router()

AVAILABLE_TIME_SLOTS = ["09:00", "11:00", "13:00", "15:00", "17:00", "19:00"]
MONTH_NAMES = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

MENU_BUTTONS = [
    "📅 Записаться на ТО", "🔍 Статус ремонта",
    "📍 Адрес и контакты", "🤖 ИИ-диагностика",
    "👨‍🔧 Связаться с деж. мастером", "💰 Прайс-лист"
]

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Записаться на ТО"), KeyboardButton(text="🔍 Статус ремонта")],
        [KeyboardButton(text="📍 Адрес и контакты"), KeyboardButton(text="🤖 ИИ-диагностика")],
        [KeyboardButton(text="👨‍🔧 Связаться с деж. мастером"), KeyboardButton(text="💰 Прайс-лист")]
    ],
    resize_keyboard=True,
    is_persistent=True
)

LATITUDE = 59.9372
LONGITUDE = 30.3130

maps_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📍 Яндекс Карты", url=f"https://yandex.ru/maps/?pt={LONGITUDE},{LATITUDE},pm2rdm&z=18&l=map"),
            InlineKeyboardButton(text="🧭 2ГИС", url=f"https://2gis.ru/spb/geo/5348651268307283?m={LONGITUDE}%2C{LATITUDE}%2F18")
        ]
    ]
)

def build_calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    today = date.today()
    cal = calendar.monthcalendar(year, month)
    keyboard = []
    month_title = f"{MONTH_NAMES[month]} {year}"
    keyboard.append([InlineKeyboardButton(text=f"📅 {month_title}", callback_data="ignore")])
    keyboard.append([InlineKeyboardButton(text=d, callback_data="ignore") for d in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]])

    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                day_date = date(year, month, day)
                if day_date < today:
                    row.append(InlineKeyboardButton(text="❌", callback_data="ignore"))
                else:
                    row.append(InlineKeyboardButton(text=str(day), callback_data=f"date:{day_date.isoformat()}"))
        keyboard.append(row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def transcribe_voice(bot, file_id: str) -> str:
    file = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file.file_path)
    audio_content = file_bytes.getvalue() if hasattr(file_bytes, "getvalue") else file_bytes.read()

    url = f"{settings.POLZA_BASE_URL.rstrip('/')}/audio/transcriptions"
    headers = {"Authorization": f"Bearer {settings.POLZA_API_KEY}"}
    
    data = aiohttp.FormData()
    data.add_field(
        name='file',
        value=audio_content,
        filename='voice.ogg',
        content_type='audio/ogg'
    )
    data.add_field(name='model', value='openai/whisper-1')

    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    res_json = await response.json()
                    return res_json.get("text", "")
                else:
                    err = await response.text()
                    print(f"❌ [DEBUG AI Voice Error]: {response.status} - {err}")
    except Exception as e:
        print(f"❌ [DEBUG AI Voice Exception]: {e}")
    return ""

async def ask_polza_ai_multimodal(content_input) -> str:
    url = f"{settings.POLZA_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.POLZA_API_KEY}",
        "Content-Type": "application/json"
    }

    if isinstance(content_input, str):
        content_payload = [{"type": "text", "text": content_input}]
    else:
        content_payload = content_input

    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты старший мастер-приёмщик автосервиса 'Восток'. "
                    "ПРАВИЛА ОТВЕТА:\n"
                    "1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО здороваться (не пиши 'Здравствуйте', 'Приветствую' и т.д.). Начинай ответ СРАЗУ с сути проблемы.\n"
                    "2. Ответ структурируй по блокам:\n"
                    "• <b>Вероятные причины:</b> 2-3 наиболее частые поломки при таких симптомах.\n"
                    "• <b>Опасность для авто:</b> можно ли аккуратно доехать своим ходом или лучше не рисковать / нужен эвакуатор.\n"
                    "• <b>Что проверим в сервисе:</b> конкретные узлы (ходовая на люфты, компьютерный сканер, замер давления и т.д.).\n"
                    "3. В самом конце напиши: 'Для точной локализации проблемы и оценки стоимости ремонта нажмите «📅 Записаться на ТО» в меню ниже.'\n"
                    "4. Тон профессиональный, чёткий, автомобильный, без лишней воды."
                )
            },
            {"role": "user", "content": content_payload}
        ],
        "temperature": 0.3
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                
                err_text = await response.text()
                print(f"❌ [DEBUG AI Chat Error]: Статус {response.status}, Ответ: {err_text}")
                return "⚠️ В данный момент сервер перегружен. Запишитесь на осмотр к мастеру через кнопку «📅 Записаться на ТО»."
    except Exception as e:
        print(f"❌ [DEBUG AI Chat Exception]: {e}")
        return "⚠️ Не удалось подключиться к серверу диагностики. Рекомендуем записаться на осмотр через главное меню."

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}!\n"
        "Вас приветствует автосервис «Восток».\n"
        "Выберите интересующий раздел меню ниже:",
        reply_markup=main_keyboard
    )

@router.message(F.text == "📍 Адрес и контакты")
async def show_contacts(message: Message, state: FSMContext):
    await state.clear()
    address_card = (
        "г. Санкт-Петербург, Невский пр., д. 1\n"
        "📞 Тел: +7 (812) 000-00-00\n"
        "⏰ 09:00 - 21:00 (без вых.)"
    )
    await message.answer_venue(
        latitude=LATITUDE,
        longitude=LONGITUDE,
        title="Автосервис «Восток»",
        address=address_card,
        reply_markup=maps_keyboard
    )

@router.message(F.text == "👨‍🔧 Связаться с деж. мастером")
async def call_duty_master(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "👨‍🔧 <b>Дежурный мастер на связи:</b>\n"
        "Telegram: @master_service\n"
        "Прямой телефон: +7 (812) 111-22-33"
    )
    await message.answer(text, reply_markup=main_keyboard, parse_mode="HTML")

@router.message(F.text == "💰 Прайс-лист")
async def show_price_list(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "💰 <b>Ориентировочный прайс-лист:</b>\n\n"
        "• Компьютерная диагностика — от 1 500 ₽\n"
        "• Замена масла и фильтра — от 1 200 ₽\n"
        "• Замена передних колодок — от 1 800 ₽\n"
        "• Регламентное ТО — от 4 500 ₽\n\n"
        "<i>Точная стоимость зависит от марки и модели автомобиля.</i>"
    )
    await message.answer(text, reply_markup=main_keyboard, parse_mode="HTML")

@router.message(F.text == "🤖 ИИ-диагностика")
async def ai_diagnostic(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AIDiagnosticStates.waiting_for_symptoms)
    text = (
        "🛠 <b>Режим умной автодиагностики</b>\n\n"
        "Опишите симптомы любым удобным способом:\n"
        "• Напишите текст с описанием проблемы (марка, модель, симптомы)\n"
        "• Отправьте фото (например, приборной панели с ошибкой)\n"
        "• Отправьте голосовое сообщение с рассказом о поломке\n\n"
        "Вы можете в любой момент нажать любую кнопку в меню ниже для выхода.\n\n"
        "<b>Если вы хотите провести ещё один анализ - еще раз нажмите на кнопку \"ИИ-диагностика\"</b>"
    )
    await message.answer(text, reply_markup=main_keyboard, parse_mode="HTML")

@router.message(AIDiagnosticStates.waiting_for_symptoms, F.text)
async def process_symptoms_text(message: Message, state: FSMContext):
    if message.text in MENU_BUTTONS:
        return
    wait_msg = await message.answer("🔧 <i>Анализирую симптомы, пожалуйста, подождите...</i>", parse_mode="HTML")
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    ai_reply = await ask_polza_ai_multimodal(message.text.strip())
    await wait_msg.delete()
    await state.clear()
    await message.answer(ai_reply, reply_markup=main_keyboard, parse_mode="HTML")

@router.message(AIDiagnosticStates.waiting_for_symptoms, F.photo)
async def process_symptoms_photo(message: Message, state: FSMContext):
    wait_msg = await message.answer("📷 <i>Анализирую изображение приборной панели / узла...</i>", parse_mode="HTML")
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(file.file_path)

    try:
        image = Image.open(file_bytes)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        max_dimension = 1024
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=75, optimize=True)
        compressed_bytes = buffer.getvalue()
    except Exception as e:
        print(f"⚠️ Ошибка сжатия фото: {e}, отправляем исходный размер")
        file_bytes.seek(0)
        compressed_bytes = file_bytes.read()

    base64_image = base64.b64encode(compressed_bytes).decode('utf-8')
    caption = message.caption or "Оцени состояние по фотографии, укажи возможные ошибки или причины."

    content_blocks = [
        {"type": "text", "text": caption},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
    ]

    ai_reply = await ask_polza_ai_multimodal(content_blocks)
    await wait_msg.delete()
    await state.clear()
    await message.answer(ai_reply, reply_markup=main_keyboard, parse_mode="HTML")

@router.message(AIDiagnosticStates.waiting_for_symptoms, F.voice)
async def process_symptoms_voice(message: Message, state: FSMContext):
    wait_msg = await message.answer("🎧 <i>Распознаю голосовое сообщение и анализирую...</i>", parse_mode="HTML")
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    recognized_text = await transcribe_voice(message.bot, message.voice.file_id)
    if not recognized_text:
        await wait_msg.delete()
        await message.answer("⚠️ Не удалось разобрать голосовое сообщение. Повторите голосом или напишите текстом.", reply_markup=main_keyboard)
        return

    ai_reply = await ask_polza_ai_multimodal(f"Пользователь надиктовал голосом симптомы: {recognized_text}")
    await wait_msg.delete()
    await state.clear()
    await message.answer(f"🗣 <i>Распознано: «{recognized_text}»</i>\n\n{ai_reply}", reply_markup=main_keyboard, parse_mode="HTML")

# --- ЗАПИСЬ НА ТО ---
@router.message(F.text == "📅 Записаться на ТО")
async def start_booking(message: Message, state: FSMContext):
    await state.clear()
    today = date.today()
    kb = build_calendar_keyboard(today.year, today.month)
    await state.set_state(BookingStates.waiting_for_date)
    await message.answer(f"Выберите желаемую дату визита ({MONTH_NAMES[today.month]} {today.year}):", reply_markup=kb)

@router.callback_query(F.data.startswith("date:"))
async def process_date_selection(callback: CallbackQuery, state: FSMContext):
    chosen_date_str = callback.data.split(":")[1]
    chosen_date = date.fromisoformat(chosen_date_str)

    loading_msg = await callback.message.edit_text("⏳ Проверяю свободное время...")
    
    existing_rows = await baserow_client.get_appointments_by_date(chosen_date_str)
    
    booked_hours = []
    for r in existing_rows:
        dt_raw = r.get("Data_Time")
        if dt_raw:
            try:
                # Очищаем Z и часовые пояса для парсинга локального времени
                dt_clean = dt_raw.split("+")[0].replace("Z", "")
                for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M"):
                    try:
                        dt_obj = datetime.strptime(dt_clean, fmt)
                        booked_hours.append(dt_obj.strftime("%H:%M"))
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

    free_slots = [slot for slot in AVAILABLE_TIME_SLOTS if slot not in booked_hours]

    today = date.today()
    if not free_slots:
        kb = build_calendar_keyboard(today.year, today.month)
        await state.set_state(BookingStates.waiting_for_date)
        await loading_msg.edit_text(
            f"❌ Извините, на {chosen_date.strftime('%d.%m.%Y')} все места заняты.\n"
            "Пожалуйста, выберите другую дату:",
            reply_markup=kb
        )
        return

    await state.update_data(chosen_date=chosen_date_str)
    await state.set_state(BookingStates.waiting_for_time)

    slot_buttons = []
    row = []
    for s in free_slots:
        row.append(InlineKeyboardButton(text=f"🕒 {s}", callback_data=f"time_{s}"))
        if len(row) == 2:
            slot_buttons.append(row)
            row = []
    if row:
        slot_buttons.append(row)

    slot_buttons.append([InlineKeyboardButton(text="⬅️ Выбрать другую дату", callback_data="change_date")])

    await loading_msg.edit_text(
        f"📅 Выбрана дата: <b>{chosen_date.strftime('%d.%m.%Y')}</b>\n"
        "Теперь выберите свободное время визита:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=slot_buttons),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "change_date")
async def back_to_calendar(callback: CallbackQuery, state: FSMContext):
    today = date.today()
    kb = build_calendar_keyboard(today.year, today.month)
    await state.set_state(BookingStates.waiting_for_date)
    await callback.message.edit_text(f"Выберите желаемую дату ({MONTH_NAMES[today.month]} {today.year}):", reply_markup=kb)

@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()

@router.callback_query(F.data.startswith("time_") | F.data.startswith("time:"))
async def process_time_selection(callback: CallbackQuery, state: FSMContext):
    raw_time = callback.data.replace("time_", "").replace("time:", "")
    chosen_time = raw_time if ":" in raw_time else f"{raw_time}:00"

    await state.update_data(chosen_time=chosen_time)
    await state.set_state(BookingStates.waiting_for_name)

    data = await state.get_data()
    chosen_date_formatted = datetime.strptime(data["chosen_date"], "%Y-%m-%d").strftime("%d.%m.%Y")

    await callback.message.edit_text(
        f"⏱ Вы выбрали: <b>{chosen_date_formatted} в {chosen_time}</b>\n\n"
        "Для подтверждения записи введите ваше <b>Фамилию и Имя</b>:",
        parse_mode="HTML"
    )

@router.message(BookingStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    if message.text in MENU_BUTTONS:
        return
    await state.update_data(client_name=message.text.strip())
    await state.set_state(BookingStates.waiting_for_car)
    await message.answer("Укажите марку и модель автомобиля:", reply_markup=main_keyboard)

@router.message(BookingStates.waiting_for_car)
async def process_car(message: Message, state: FSMContext):
    if message.text in MENU_BUTTONS:
        return
    await state.update_data(client_car=message.text.strip())
    await state.set_state(BookingStates.waiting_for_trouble)
    await message.answer("Опишите неисправность или причину обращения:", reply_markup=main_keyboard)

@router.message(BookingStates.waiting_for_trouble)
async def process_trouble(message: Message, state: FSMContext):
    if message.text in MENU_BUTTONS:
        return
    data = await state.get_data()
    trouble_desc = message.text.strip()
    user_id = message.from_user.id

    time_part = data["chosen_time"] if ":" in data["chosen_time"] else f"{data['chosen_time']}:00"
    
    # Явно передаём смещение +03:00, чтобы сервер Baserow не смещал время в UTC
    iso_datetime = f"{data['chosen_date']}T{time_part}:00+03:00"

    await baserow_client.create_appointment(
        client_name=data["client_name"],
        date_time_iso=iso_datetime,
        notes=trouble_desc,
        avto=data["client_car"],
        telegram_id=user_id
    )

    await state.clear()
    chosen_dt = datetime.strptime(f"{data['chosen_date']} {time_part}", "%Y-%m-%d %H:%M")

    await message.answer(
        f"✅ <b>Вы успешно записаны!</b>\n\n"
        f"📅 <b>Дата:</b> {chosen_dt.strftime('%d.%m.%Y')}\n"
        f"⏰ <b>Время:</b> {chosen_dt.strftime('%H:%M')}\n"
        f"👤 <b>Клиент:</b> {data['client_name']}\n"
        f"🚗 <b>Автомобиль:</b> {data['client_car']}\n"
        f"🛠 <b>Причина обращения:</b> {trouble_desc}\n\n"
        f"Ждём вас в назначенное время!",
        reply_markup=main_keyboard,
        parse_mode="HTML"
    )

# --- ПРОВЕРКА СТАТУСА ---
@router.message(F.text == "🔍 Статус ремонта")
async def check_status(message: Message, state: FSMContext):
    await state.clear()
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    appointment = await baserow_client.get_latest_client_appointment(message.from_user.id)

    if not appointment:
        await message.answer("У вас пока нет активных обращений.", reply_markup=main_keyboard)
        return

    raw_dt = appointment.get("Data_Time", "") or ""
    date_part = "—"
    time_part = "—"
    if raw_dt:
        dt_clean = raw_dt.split("+")[0].replace("Z", "")
        for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
            try:
                dt_obj = datetime.strptime(dt_clean, fmt)
                date_part = dt_obj.strftime("%d.%m.%Y")
                time_part = dt_obj.strftime("%H:%M")
                break
            except ValueError:
                continue

    client_name = appointment.get("Name") or "Не указан"
    avto_name = appointment.get("Avto") or "Не указан"

    status_raw = appointment.get("Status")
    if isinstance(status_raw, list) and status_raw:
        status_text = status_raw[0].get("value", "Запланирован визит")
    elif isinstance(status_raw, dict):
        status_text = status_raw.get("value", "Запланирован визит")
    elif status_raw:
        status_text = str(status_raw)
    else:
        status_text = "Запланирован визит"

    notes_raw = appointment.get("Notes", "") or ""
    if "[TG:" in notes_raw and "]" in notes_raw:
        trouble_text = notes_raw.split("]", 1)[-1].strip()
    else:
        trouble_text = notes_raw.strip()
    if not trouble_text:
        trouble_text = "Не указана"

    response_text = (
        f"📋 <b>Данные вашей записи:</b>\n\n"
        f"📅 <b>Дата:</b> {date_part}\n"
        f"⏰ <b>Время:</b> {time_part}\n"
        f"👤 <b>Клиент:</b> {client_name}\n"
        f"🚗 <b>Автомобиль:</b> {avto_name}\n"
        f"🛠 <b>Причина обращения:</b> {trouble_text}\n"
        f"📌 <b>Статус ремонта:</b> {status_text}"
    )

    await message.answer(
        response_text,
        reply_markup=main_keyboard,
        parse_mode="HTML"
    )

