import asyncio
import os
from datetime import timezone
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Загружаем переменные окружения из .env
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Импорт моделей/БД утилит
from models import init_db, get_session, ensure_user_started


@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    # Фиксируем старт пользователя в БД (идемпотентно)
    try:
        # Время запуска из Telegram (UTC). Делаем datetime timezone-aware при необходимости
        started_at = message.date
        if started_at and started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)

        with get_session() as session:
            ensure_user_started(
                session,
                telegram_id=message.from_user.id,
                started_at=started_at,
            )
    except Exception as e:
        # Логируем, но не падаем, чтобы пользователь получил ответ
        print(f"DB error on /start: {e}")

    await message.answer("Привет! Я бот Neuron_AI")


async def main():
    # Создаем таблицы при запуске (если их еще нет)
    try:
        init_db()
    except Exception as e:
        print(f"DB init error: {e}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
