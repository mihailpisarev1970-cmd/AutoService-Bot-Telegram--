import aiohttp
from typing import Optional, List, Dict, Any
from config import settings

BASE_URL = settings.BASEROW_URL.rstrip('/')
HEADERS = {
    "Authorization": f"Token {settings.BASEROW_TOKEN}",
    "Content-Type": "application/json"
}

async def get_appointments_by_date(date_str: str) -> List[Dict[str, Any]]:
    """Ищет записи на указанную дату по колонке Data_Time."""
    url = f"{BASE_URL}/api/database/rows/table/{settings.BASEROW_TABLE_ID}/"
    params = {
        "user_field_names": "true",
        "size": 100,
        "filter__Data_Time__contains": date_str
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("results", [])
            return []

async def create_appointment(client_name: str, date_time_iso: str, notes: str, avto: str, telegram_id: int) -> bool:
    """Создает новую запись в таблице Avto_appointment."""
    url = f"{BASE_URL}/api/database/rows/table/{settings.BASEROW_TABLE_ID}/?user_field_names=true"
    
    full_notes = f"[TG:{telegram_id}] {notes}".strip()

    payload = {
        "Name": client_name,
        "Data_Time": date_time_iso,
        "Notes": full_notes,
        "Avto": avto,
        "Status": "Запланирован визит"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=HEADERS, json=payload) as resp:
            return resp.status in (200, 201)

async def get_latest_client_appointment(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Получает записи из Baserow и возвращает самую свежую запись клиента."""
    url = f"{BASE_URL}/api/database/rows/table/{settings.BASEROW_TABLE_ID}/"
    params = {
        "user_field_names": "true",
        "size": 100
    }
    
    tg_str = str(telegram_id)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                results = data.get("results", [])
                
                # Ищем все записи пользователя и берём последнюю
                user_appointments = [
                    row for row in results 
                    if tg_str in str(row.get("Notes") or "")
                ]
                
                if user_appointments:
                    # Возвращаем последнюю добавленную запись
                    return user_appointments[-1]
            else:
                text_err = await resp.text()
                print(f"Ошибка запроса в Baserow: {resp.status} - {text_err}")
                
    return None