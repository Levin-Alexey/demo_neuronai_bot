"""Обработчик кнопки 'Быстрый подбор'"""

from aiogram import types, F, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()


@router.message(F.text == "🔥 Быстрый подбор")
async def quick_search_handler(message: types.Message):
    """Обработчик для быстрого подбора кандидатов"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "🔥 <b>Быстрый подбор</b>\n\nФункционал в разработке...",
        parse_mode="HTML",
        reply_markup=keyboard
    )


def register_handlers(main_router):
    """Регистрация обработчиков быстрого подбора"""
    main_router.include_router(router)

