"""Обработчик кнопки 'Анализ резюме (CV Scan)'"""

from aiogram import types, F, Router

router = Router()


@router.message(F.text == "📄 Анализ резюме (CV Scan)")
async def cv_scan_handler(message: types.Message):
    """Обработчик для анализа резюме"""
    await message.answer("📄 <b>Анализ резюме (CV Scan)</b>\n\nФункционал в разработке...", parse_mode="HTML")


def register_handlers(main_router):
    """Регистрация обработчиков анализа резюме"""
    main_router.include_router(router)

