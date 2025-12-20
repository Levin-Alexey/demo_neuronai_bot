"""Заглушка обработчика кнопки Как подключить"""

from aiogram import Router, F, types

router = Router()


@router.message(F.text == "❓ Как подключить")
async def how_to_connect_handler(message: types.Message):
    await message.answer("❓ Как подключить: функционал в разработке")


def register_handlers(parent_router: Router):
    parent_router.include_router(router)

