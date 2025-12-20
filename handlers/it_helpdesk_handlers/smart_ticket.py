"""Заглушка обработчика кнопки Умный Тикет"""

from aiogram import Router, F, types

router = Router()


@router.message(F.text == "📋 Умный Тикет")
async def smart_ticket_handler(message: types.Message):
    await message.answer("📋 Умный Тикет: функционал в разработке")


def register_handlers(parent_router: Router):
    parent_router.include_router(router)

