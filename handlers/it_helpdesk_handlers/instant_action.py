"""Заглушка обработчика кнопки Мгновенное действие"""

from aiogram import Router, F, types

router = Router()


@router.message(F.text == "⚡ Мгновенное действие")
async def instant_action_handler(message: types.Message):
    await message.answer("⚡ Мгновенное действие: функционал в разработке")


def register_handlers(parent_router: Router):
    parent_router.include_router(router)

