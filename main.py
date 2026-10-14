import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import settings
from handlers import router

async def main():
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    
    dp.include_router(router)
    
    print("🚀 Бот автосервиса успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")