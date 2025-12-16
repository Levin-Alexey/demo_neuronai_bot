"""Обработчик кнопки IT HelpDesk"""

from aiogram import types, F, Router

router = Router()


@router.message(F.text == "🛠 IT HelpDesk")
async def it_helpdesk_handler(message: types.Message):
    """Обработчик кнопки IT HelpDesk"""
    await message.answer("Раздел 🛠 IT HelpDesk\n\nФункционал в разработке...")


def register_handlers(dp):
    """Регистрация обработчиков IT HelpDesk"""
    dp.include_router(router)

