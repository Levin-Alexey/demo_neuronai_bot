"""Обработчик кнопки База Знаний"""

from aiogram import types, F, Router

router = Router()


@router.message(F.text == "🧠 База Знаний")
async def knowledge_base_handler(message: types.Message):
    """Обработчик кнопки База Знаний"""
    await message.answer("Раздел 🧠 База Знаний\n\nФункционал в разработке...")


def register_handlers(dp):
    """Регистрация обработчиков Базы Знаний"""
    dp.include_router(router)

