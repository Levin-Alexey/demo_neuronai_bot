"""Кнопки меню IT HelpDesk"""

from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from handlers.it_helpdesk_handlers import ai_eye, instant_action, smart_ticket, how_to_connect, back_menu

router = Router()


@router.message(F.text == "🛠 IT HelpDesk")
async def it_helpdesk_menu(message: types.Message):
    """Отображает меню IT HelpDesk с основными действиями."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 AI-Глаз")],
            [KeyboardButton(text="⚡ Мгновенное действие")],
            [KeyboardButton(text="📋 Умный Тикет")],
            [KeyboardButton(text="❓ Как подключить")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True
    )
    await message.answer("Это раздел IT Поддержки", reply_markup=keyboard)


def register_handlers(parent_router: Router):
    """Регистрирует меню IT HelpDesk в родительском роутере."""
    parent_router.include_router(router)
    ai_eye.register_handlers(parent_router)
    instant_action.register_handlers(parent_router)
    smart_ticket.register_handlers(parent_router)
    how_to_connect.register_handlers(parent_router)
    back_menu.register_handlers(parent_router)
