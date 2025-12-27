"""Регистрация подменю Охраны труда."""

from aiogram import Router

from . import photo_control, work_permit, report_violation, bot_instructor, back_menu


def register_handlers(parent_router: Router):
    """Регистрирует обработчики разделов Охраны труда в родительском роутере."""
    photo_control.register_handlers(parent_router)
    work_permit.register_handlers(parent_router)
    report_violation.register_handlers(parent_router)
    bot_instructor.register_handlers(parent_router)
    back_menu.register_handlers(parent_router)

