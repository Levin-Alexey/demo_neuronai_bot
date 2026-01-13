import asyncio
import os
from datetime import timezone
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, TelegramObject
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from typing import Callable, Dict, Any, Awaitable

# Загружаем переменные окружения из .env
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в .env файле")

# Импортируем состояния
from states import BotStates

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# ==================== Middleware для проверки доступа ====================


class AccessCheckMiddleware(BaseMiddleware):
    """Middleware для проверки доступа пользователя к боту (24 часа с момента /start)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем message из event
        event_update = data.get('event_update')
        if not event_update:
            return await handler(event, data)
        
        message = getattr(event_update, 'message', None) or \
                  getattr(event_update, 'callback_query', None)
        
        if not message:
            return await handler(event, data)
        
        # Пропускаем команду /start
        if hasattr(message, 'text') and message.text and \
           message.text.startswith('/start'):
            return await handler(event, data)
        
        if not message.from_user:
            return await handler(event, data)
            
        telegram_id = message.from_user.id
        
        # Проверяем доступ
        try:
            with get_session() as session:
                has_access, access_until = check_user_access(session, telegram_id)
                
                if not has_access:
                    # Доступ истек - показываем сообщение
                    kb = ReplyKeyboardMarkup(
                        keyboard=[
                            [KeyboardButton(
                                text="👤 Связаться с менеджером")],
                            [KeyboardButton(
                                text="🔄 Проверить доступ")]
                        ],
                        resize_keyboard=True
                    )
                    
                    access_until_str = ""
                    if access_until:
                        from datetime import timedelta
                        # MSK (настройте под свой пояс)
                        local_time = access_until + timedelta(hours=3)
                        access_until_str = local_time.strftime(
                            "%d.%m.%Y в %H:%M")
                    
                    msg = (
                        f"⏰ <b>Доступ к боту истек</b>\n\n"
                        f"Ваш пробный период (24 часа) "
                        f"закончился {access_until_str}.\n\n"
                        f"🔹 Чтобы продолжить использование бота, "
                        f"свяжитесь с менеджером\n"
                        f"🔹 Нажмите кнопку ниже или используйте "
                        f"команду /manager"
                    )
                    
                    await message.answer(
                        msg,
                        parse_mode="HTML",
                        reply_markup=kb
                    )
                    return  # Блокируем дальнейшую обработку
        except Exception as e:
            print(f"Access check error: {e}")
            # В случае ошибки БД - пропускаем проверку
            pass
        
        return await handler(event, data)

# Импорт моделей/БД утилит
from models import init_db, get_session, ensure_user_started, check_user_access
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


@dp.message(F.text == "🔄 Проверить доступ")
async def check_access_status(message: types.Message, state: FSMContext):
    """Проверить статус доступа пользователя."""
    try:
        with get_session() as session:
            has_access, access_until = check_user_access(session, message.from_user.id)
            
            if has_access and access_until:
                from datetime import timedelta, datetime
                now = datetime.now(timezone.utc)
                time_left = access_until - now
                hours_left = int(time_left.total_seconds() / 3600)
                minutes_left = int((time_left.total_seconds() % 3600) / 60)
                
                # Локальное время
                local_time = access_until + timedelta(hours=3)  # MSK
                access_until_str = local_time.strftime("%d.%m.%Y в %H:%M")
                
                await message.answer(
                    f"✅ <b>Доступ активен</b>\n\n"
                    f"⏰ Осталось времени: {hours_left} ч. {minutes_left} мин.\n"
                    f"📅 Доступ до: {access_until_str}\n\n"
                    f"Вы можете продолжить использование бота.",
                    parse_mode="HTML"
                )
            else:
                kb = ReplyKeyboardMarkup(
                    keyboard=[[
                        KeyboardButton(text="👤 Связаться с менеджером")
                    ]],
                    resize_keyboard=True
                )
                await message.answer(
                    "⏰ <b>Доступ истек</b>\n\n"
                    "Для продления доступа свяжитесь с менеджером.",
                    parse_mode="HTML",
                    reply_markup=kb
                )
    except Exception as e:
        await message.answer(f"Ошибка при проверке доступа: {e}")


@dp.message(F.text == "👤 Связаться с менеджером")
async def contact_manager_expired(message: types.Message, state: FSMContext):
    """Обработчик кнопки 'Связаться с менеджером' для пользователей с истекшим доступом."""
    from handlers.ai_manager import ManagerState
    
    await state.set_state(ManagerState.waiting_for_message)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

    await message.answer(
        "📞 <b>Связь с менеджером</b>\n\n"
        "Напишите Ваше сообщение. Вы можете отправить текст, файл или фото.\n"
        "Менеджер ответит Вам в ближайшее время.",
        parse_mode="HTML",
        reply_markup=kb
    )


async def main():
    # Создаем таблицы при запуске (если их еще нет)
    try:
        init_db()
    except Exception as e:
        print(f"DB init error: {e}")

    # Регистрируем middleware для проверки доступа
    dp.message.middleware(AccessCheckMiddleware())
    
    # Регистрируем обработчики кнопок
    hr.register_handlers(dp)
    labor_safety.register_handlers(dp)
    it_helpdesk.register_handlers(dp)
    knowledge_base.register_handlers(dp)
    ai_manager.register_handlers(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
