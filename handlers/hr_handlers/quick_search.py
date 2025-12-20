"""Обработчик кнопки 'Быстрый подбор'"""

import asyncio
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()


class QuickSearchState(StatesGroup):
    """Состояния FSM для быстрого подбора."""
    waiting_for_action = State()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены для режима подбора."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


def get_hr_keyboard() -> ReplyKeyboardMarkup:
    """Базовое меню HR отдела."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎭 Пройти собеседование")],
            [KeyboardButton(text="📄 Анализ резюме (CV Scan)")],
            [KeyboardButton(text="🔥 Быстрый подбор")],
            [KeyboardButton(text="⚙️ Информация для HR")],
            [KeyboardButton(text="🔙 Назад в меню")],
        ],
        resize_keyboard=True,
    )


@router.message(F.text == "🔥 Быстрый подбор")
async def start_fast_search_demo(message: types.Message, state: FSMContext) -> None:
    """Демонстрация быстрого подбора с имитацией работы ИИ."""

    await state.set_state(QuickSearchState.waiting_for_action)

    # 1. Отправляем вводное продающее сообщение
    await message.answer(
        "⚡ <b>Демо: Быстрый подбор (Flash Search)</b>\n\n"
        "В реальности поиск — это воронка из 100+ резюме. Моя задача — сделать всю черновую работу и оставить вам только <b>Топ-3 идеальных матча</b>.\n\n"
        "🚀 <b>В чем ценность модуля:</b>\n"
        "🔹 Агрегация баз (HH, Telegram, LinkedIn)\n"
        "🔹 Авто-фильтр неадекватных откликов\n"
        "🔹 Выдача только тех, кого стоит звать на звонок\n\n"
        "👇 <b>Запускаю демонстрацию на примере вакансии «Менеджер по продажам»...</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )

    # Небольшая пауза для чтения
    await asyncio.sleep(1.5)

    # 2. Эффект "Работающего ИИ" (изменяющееся сообщение)
    status_msg = await message.answer(
        "🔄 <i>Подключение к базам кандидатов...</i>",
        parse_mode="HTML"
    )

    steps = [
        "🔍 <i>Сканирование источников (HH, LinkedIn, TG)...</i>",
        "🧠 <i>Найдено 142 анкеты. Анализирую опыт...</i>",
        "🗑 <i>Отсев нерелевантных... (осталось 12)</i>",
        "⭐ <i>Выбор лучших по Soft Skills...</i>",
        "✅ <b>Готово! Подобран Топ-1 кандидат.</b>"
    ]

    for step in steps:
        await asyncio.sleep(1.0)  # Пауза между этапами (1 секунда)
        try:
            await status_msg.edit_text(step, parse_mode="HTML")
        except Exception:
            pass  # Игнорируем ошибки, если юзер удалил чат и т.д.

    # 3. Отправляем "Карточку Героя"
    candidate_text = (
        "🏆 <b>Кандидат #1: Елена В.</b>\n"
        "<i>Менеджер по продажам (B2B)</i>\n\n"
        "📊 <b>AI-Скоринг: 9.8 / 10</b>\n"
        "└ <i>Идеальное попадание в профиль «Охотник»</i>\n\n"
        "💎 <b>Почему она:</b>\n"
        "• <b>Результат:</b> В прошлом месте увеличила выручку на 40% за полгода.\n"
        "• <b>Скиллы:</b> Работает в amoCRM, не боится холодных звонков, отличный английский.\n"
        "• <b>Психотип:</b> Достигатор, высокая стрессоустойчивость.\n\n"
        "💰 <b>Ожидания:</b> 120 000 руб.\n"
        "📅 <b>Готова выйти:</b> Завтра"
    )

    # Удаляем сообщение о загрузке, чтобы не мешало
    await status_msg.delete()

    # Отправляем результат (Фото + Описание)
    photo_url = (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/"
        "Businesswoman_icon_%28Noun_Project%29.svg/1024px-"
        "Businesswoman_icon_%28Noun_Project%29.svg.png"
    )

    try:
        await message.answer_photo(
            photo=photo_url,
            caption=candidate_text,
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
    except Exception:
        # Фоллбэк: если Telegram не смог скачать картинку
        await message.answer(
            candidate_text,
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )


@router.message(QuickSearchState.waiting_for_action, F.text == "❌ Отмена")
async def cancel_fast_search(message: types.Message, state: FSMContext) -> None:
    """Отмена быстрого подбора."""
    await state.clear()
    await message.answer(
        "Быстрый подбор отменен.",
        reply_markup=get_hr_keyboard(),
    )


def register_handlers(main_router: Router) -> None:
    """Регистрация обработчиков быстрого подбора."""
    main_router.include_router(router)
