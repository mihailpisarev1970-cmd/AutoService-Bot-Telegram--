from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(
    api_key=settings.POLZA_API_KEY,
    base_url=settings.POLZA_BASE_URL
)

SYSTEM_PROMPT = """
Ты — опытный старший мастер-диагност автосервиса.
Клиент описывает симптомы неисправности автомобиля. Твоя задача:
1. Выделить 2-3 наиболее вероятные причины поломки.
2. Оценить критичность (можно ли ехать дальше или нужен срочный визит/эвакуатор).
3. Дать четкую рекомендацию, какой узел нужно осмотреть на сервисе в первую очередь.

Форматируй ответ кратко, понятно, маркированным списком. Напомни, что финальный диагноз ставится только при очном осмотре в автосервисе.
"""

async def analyze_car_issue(user_text: str) -> str:
    try:
        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.4,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        return "⚠️ Не удалось связаться с сервисом диагностики. Пожалуйста, обратитесь к дежурному мастеру."
