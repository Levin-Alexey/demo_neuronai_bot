"""Обработчик кнопки HR и Найм"""

import os
from aiogram import types, F, Router
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton

router = Router()


@router.message(F.text == "🤝 HR и найм")
async def hr_handler(message: types.Message):
    """Обработчик кнопки HR и Найм"""
    # Отправляем видео-кружочек (Video Note)
    video_path = "src/1218.mp4"
    if os.path.exists(video_path):
        video = FSInputFile(video_path)
        await message.answer_video_note(video)
    else:
        await message.answer("Видео не найдено")

    # Отправляем сообщение с описанием возможностей
    hr_text = """👔 Департамент Найма и Оценки

Добро пожаловать в HR-отдел будущего.

Здесь нет "человеческого фактора", усталости и предвзятости.

Мои возможности в демо-режиме:

    <b>Собеседование</b>: Попробуйте обмануть меня или пройти отбор на должность

    <b>Анализ</b>: Загрузите любой файл резюме, и я найду в нем "красные флаги"

    <b>Подбор</b>: Покажу, как выглядит идеальная выдача кандидатов

👇 Что запустим первым?"""

    # Создаем клавиатуру для HR департамента
    hr_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎭 Пройти собеседование")],
            [KeyboardButton(text="📄 Анализ резюме (CV Scan)")],
            [KeyboardButton(text="🔥 Быстрый подбор")],
            [KeyboardButton(text="⚙️ Информация для HR")],
            [KeyboardButton(text="🔙 Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(hr_text, parse_mode="HTML", reply_markup=hr_keyboard)


def register_handlers(dp):
    """Регистрация обработчиков HR"""
    from handlers.hr_handlers import interview, cv_scan, quick_search, hr_info, back_menu

    dp.include_router(router)
    # Регистрируем все HR подобработчики
    interview.register_handlers(router)
    cv_scan.register_handlers(router)
    quick_search.register_handlers(router)
    hr_info.register_handlers(router)
    back_menu.register_handlers(router)

