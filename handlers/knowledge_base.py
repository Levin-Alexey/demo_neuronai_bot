"""Обработчик кнопки База Знаний"""

import os
from aiogram import types, F, Router
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from states import BotStates

router = Router()


@router.message(F.text == "🧠 База Знаний")
async def knowledge_base_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки База Знаний"""
    # Отправляем видео-кружочек (Video Note)
    video_path = "src/2026_1.mp4"
    if os.path.exists(video_path):
        video = FSInputFile(video_path)
        await message.answer_video_note(video)
    else:
        await message.answer("Видео не найдено")

    # Отправляем сообщение с описанием возможностей
    kb_text = """🧠 Раздел База Знаний

Добро пожаловать в базу знаний организации.

Здесь вы найдете все необходимые регламенты, процедуры и обучающие материалы.

Мои возможности в демо-режиме:

    <b>🔎 Найти ответ</b>: Быстрый поиск по регламентам и нормативным документам

    <b>🚀 Курс молодого бойца</b>: Обучающий курс для новых сотрудников

    <b>📂 Библиотека</b>: Полный каталог документов и инструкций

👇 Что запустим первым?"""

    # Создаем клавиатуру для раздела База Знаний
    kb_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔎 Найти ответ")],
            [KeyboardButton(text="🚀 Курс молодого бойца")],
            [KeyboardButton(text="📂 Библиотека")],
            [KeyboardButton(text="🔙 Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(kb_text, parse_mode="HTML", reply_markup=kb_keyboard)

    # Устанавливаем состояние меню База Знаний
    await state.set_state(BotStates.KNOWLEDGE_BASE_MENU)


def register_handlers(dp):
    """Регистрация обработчиков Базы Знаний"""
    from handlers.knowledge_base_handlers import search_answer, rookie_course, library, back_menu

    dp.include_router(router)
    # Регистрируем все подобработчики
    search_answer.register_handlers(router)
    rookie_course.register_handlers(router)
    library.register_handlers(router)
    back_menu.register_handlers(router)

