"""Обработчик кнопки 'Назад в меню'"""

from aiogram import types, F, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру главного меню"""
    return ReplyKeyboardMarkup(
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


@router.message(F.text == "🔙 Назад в меню")
async def back_to_menu_handler(message: types.Message):
    """Обработчик для возврата в главное меню"""
    await message.answer(
        "🏠 Выберите отдел, который хотите автоматизировать:",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "◀️ Назад")
async def back_button_handler(message: types.Message):
    """Обработчик кнопки ◀️ Назад - возврат в меню HR"""
    user = message.from_user
    if not user:
        return

    telegram_id = user.id

    # Проверяем, не в собеседовании ли пользователь
    try:
        from handlers.hr_handlers.interview import is_in_interview, end_session, call_n8n

        if is_in_interview(telegram_id):
            # Уведомляем n8n о завершении
            await call_n8n({
                "action": "cancel",
                "telegram_id": telegram_id,
            })
            # Завершаем сессию
            end_session(telegram_id)
    except Exception as e:
        print(f"Error ending interview session: {e}")

    # Возвращаем в меню HR
    hr_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎭 Пройти собеседование")],
            [KeyboardButton(text="📄 Анализ резюме (CV Scan)")],
            [KeyboardButton(text="🔥 Быстрый подбор")],
            [KeyboardButton(text="⚙️ Информация для HR")],
            [KeyboardButton(text="🔙 Назад в меню")]
        ],
        resize_keyboard=True
    )

    hr_text = """👔 Департамент Найма и Оценки

Добро пожаловать в HR-отдел будущего.

👇 Что запустим?"""

    await message.answer(hr_text, reply_markup=hr_keyboard)


def register_handlers(main_router):
    """Регистрация обработчиков возврата в меню"""
    main_router.include_router(router)

