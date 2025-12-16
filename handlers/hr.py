"""Обработчик кнопки HR и Найм"""

from aiogram import types, F, Router

router = Router()


@router.message(F.text == "🤝 HR и Найм")
async def hr_handler(message: types.Message):
    """Обработчик кнопки HR и Найм"""
    await message.answer("Раздел 🤝 HR и Найм\n\nФункционал в разработке...")


def register_handlers(dp):
    """Регистрация обработчиков HR"""
    dp.include_router(router)

