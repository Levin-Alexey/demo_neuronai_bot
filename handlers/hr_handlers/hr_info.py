"""Обработчик кнопки 'Информация для HR'"""

from aiogram import types, F, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()


@router.message(F.text == "⚙️ Информация для HR")
async def hr_info_handler(message: types.Message):
    """Обработчик для информации о HR департаменте"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "⚙️ <b>Информация для HR</b>\n\nФункционал в разработке...",
        parse_mode="HTML",
        reply_markup=keyboard
    )


def register_handlers(main_router):
    """Регистрация обработчиков информации для HR"""
    main_router.include_router(router)

