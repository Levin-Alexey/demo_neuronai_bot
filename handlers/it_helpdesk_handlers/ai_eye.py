"""Заглушка обработчика кнопки AI-Глаз"""

from aiogram import Router, F, types

router = Router()


@router.message(F.text == "🔍 AI-Глаз")
async def ai_eye_handler(message: types.Message):
    await message.answer("🔍 AI-Глаз: функционал в разработке")


def register_handlers(parent_router: Router):
    parent_router.include_router(router)

