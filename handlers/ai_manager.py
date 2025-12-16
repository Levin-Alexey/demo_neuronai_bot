"""Обработчик кнопки AI-Менеджер"""

from aiogram import types, F, Router

router = Router()


@router.message(F.text == "💰 AI-Менеджер")
async def ai_manager_handler(message: types.Message):
    """Обработчик кнопки AI-Менеджер"""
    await message.answer("Раздел 💰 AI-Менеджер\n\nФункционал в разработке...")


def register_handlers(dp):
    """Регистрация обработчиков AI-Менеджера"""
    dp.include_router(router)

