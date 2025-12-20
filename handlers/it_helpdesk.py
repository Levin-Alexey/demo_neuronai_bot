"""Обработчик кнопки IT HelpDesk"""

from aiogram import Router

from handlers.it_helpdesk_handlers import menu

router = Router()


def register_handlers(dp):
    """Регистрация обработчиков IT HelpDesk"""
    dp.include_router(router)
    # Регистрируем подменю IT HelpDesk
    menu.register_handlers(router)
