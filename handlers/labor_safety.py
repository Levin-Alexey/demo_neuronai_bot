"""Обработчик кнопки Охрана труда"""

from aiogram import types, F, Router

router = Router()


@router.message(F.text == "👷‍♂️ Охрана труда")
async def labor_safety_handler(message: types.Message):
    """Обработчик кнопки Охрана труда"""
    await message.answer("Раздел 👷‍♂️ Охрана труда\n\nФункционал в разработке...")


def register_handlers(dp):
    """Регистрация обработчиков Охраны труда"""
    dp.include_router(router)

