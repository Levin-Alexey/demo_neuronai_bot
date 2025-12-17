"""Обработчик кнопки 'Назад в меню'"""

from aiogram import types, F, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()


@router.message(F.text == "🔙 Назад в меню")
async def back_to_menu_handler(message: types.Message):
    """Обработчик для возврата в главное меню"""
    # Создаем главную клавиатуру
    main_keyboard = ReplyKeyboardMarkup(
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

    await message.answer(
        "🏠 Главное меню\n\nВыберите отдел:",
        reply_markup=main_keyboard
    )


def register_handlers(main_router):
    """Регистрация обработчиков возврата в меню"""
    main_router.include_router(router)

