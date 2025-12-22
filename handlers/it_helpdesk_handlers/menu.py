"""Регистрация подменю IT HelpDesk."""

from aiogram import Router

from handlers.it_helpdesk_handlers import ai_eye, instant_action, smart_ticket, how_to_connect, back_menu


def register_handlers(parent_router: Router):
    """Регистрирует обработчики разделов IT HelpDesk в родительском роутере."""
    ai_eye.register_handlers(parent_router)
    instant_action.register_handlers(parent_router)
    smart_ticket.register_handlers(parent_router)
    how_to_connect.register_handlers(parent_router)
    back_menu.register_handlers(parent_router)
