import asyncio
import os
from datetime import timezone
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

# Загружаем переменные окружения из .env
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

# Импортируем состояния
from states import BotStates

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Импорт моделей/БД утилит
from models import init_db, get_session, ensure_user_started
# Импорт обработчиков
from handlers import hr, labor_safety, it_helpdesk, knowledge_base, ai_manager


@dp.message(Command('start'))
async def cmd_start(message: types.Message, state: FSMContext):
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
                KeyboardButton(text="🤝 HR и найм"),
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

    # Отправляем видео кружочком (Video Note)
    video_path = "src/1217.mp4"
    if os.path.exists(video_path):
        video = FSInputFile(video_path)
        await message.answer_video_note(video)
    else:
        await message.answer("Видео не найдено", reply_markup=keyboard)


    # Отправляем сообщение с инструкцией
    instruction_text = """Теперь Ваша очередь управлять. Перед вами пульт управления цифровым офисом. Какую задачу автоматизируем первой? Выберите департамент в меню, и ИИ-агент моментально вступит в диалог 👇 

Выберите отдел для запуска демо-режима:

👔 <b>HR и найм</b> - Проведите собеседование и оцените кандидата.

👷‍♂️ <b>Охрана труда</b> - Ваши сотрудники всегда в безопасности.

🛠 <b>IT HelpDesk</b> - Решите тех. проблему за 10 секунд.

🧠 <b>База Знаний</b> - Найдите ответ в регламентах или пройдите тест.

💰 <b>AI-Менеджер</b> - Попробуйте «отказать» боту в продаже.

Нажмите на кнопку ниже, чтобы активировать нужного сотрудника ⤵️"""

    await message.answer(instruction_text, parse_mode="HTML", reply_markup=keyboard)

    # Устанавливаем состояние главного меню
    await state.set_state(BotStates.MAIN_MENU)


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
