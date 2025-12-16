import asyncio
import os
from datetime import timezone
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

# Загружаем переменные окружения из .env
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Импорт моделей/БД утилит
from models import init_db, get_session, ensure_user_started
# Импорт обработчиков
from handlers import hr, labor_safety, it_helpdesk, knowledge_base, ai_manager


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

    # Создаем клавиатуру с кнопками
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🤝 HR и Найм"),
                KeyboardButton(text="👷‍♂️ Охрана труда"),
            ],
            [
                KeyboardButton(text="🛠 IT HelpDesk"),
                KeyboardButton(text="🧠 База Знаний"),
            ],
            [
                KeyboardButton(text="💰 AI-Менеджер"),
            ]
        ],
        resize_keyboard=True
    )

    # Отправляем видео с клавиатурой
    video_path = "src/Neira.mp4"
    if os.path.exists(video_path):
        video = FSInputFile(video_path)
        await message.answer_video(video, reply_markup=keyboard)
    else:
        await message.answer("Видео не найдено", reply_markup=keyboard)


async def main():
    # Создаем таблицы при запуске (если их еще нет)
    try:
        init_db()
    except Exception as e:
        print(f"DB init error: {e}")

    # Регистрируем обработчики кнопок
    hr.register_handlers(dp)
    labor_safety.register_handlers(dp)
    it_helpdesk.register_handlers(dp)
    knowledge_base.register_handlers(dp)
    ai_manager.register_handlers(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
