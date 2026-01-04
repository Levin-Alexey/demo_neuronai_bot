"""Обработчик кнопки 'Сообщить о нарушении' (DEMO-режим, без N8N)."""

import asyncio
import random
import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

logger = logging.getLogger(__name__)
router = Router()

# --- Состояния (Шаги опроса) ---
class ReportViolationState(StatesGroup):
    WAITING_FOR_VIOLATION_TYPE = State()
    WAITING_FOR_LOCATION = State()
    WAITING_FOR_DESCRIPTION = State()
    WAITING_FOR_PHOTO = State()

# --- Клавиатуры ---
def _safety_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню охраны труда."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 Получить допуск")],
            [KeyboardButton(text="📝 Оформить работы")],
            [KeyboardButton(text="🆘 Сообщить о нарушении")],
            [KeyboardButton(text="🧠 Бот-Инструктор")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )

def _violation_types_keyboard() -> ReplyKeyboardMarkup:
    """Типы нарушений."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚠️ Нарушение ТБ")],
            [KeyboardButton(text="🦺 Нет каски/жилета")],
            [KeyboardButton(text="🔥 Пожарная опасность")],
            [KeyboardButton(text="⚡ Электрика")],
            [KeyboardButton(text="🏗 Оборудование")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )

# --- 1. Старт сценария ---
@router.message(F.text == "🆘 Сообщить о нарушении")
async def report_violation_handler(message: types.Message, state: FSMContext):
    await state.set_state(ReportViolationState.WAITING_FOR_VIOLATION_TYPE)

    # Красивое описание раздела
    intro_text = (
        "🆘 <b>Система оперативного реагирования (Incognito)</b>\n\n"
        "Ваша бдительность — залог общей безопасности. Не проходите мимо нарушений.\n\n"
        "🛡 <b>Как это работает:</b>\n"
        "1. Вы фиксируете факт нарушения (можно анонимно).\n"
        "2. Система присваивает инциденту <b>Красный приоритет</b>.\n"
        "3. Информация мгновенно передается начальнику участка и в службу ТБ.\n\n"
        "👇 <b>Выберите категорию, чтобы начать:</b>"
    )

    await message.answer(
        intro_text,
        parse_mode="HTML",
        reply_markup=_violation_types_keyboard(),
    )

# --- 2. Выбор типа ---
@router.message(ReportViolationState.WAITING_FOR_VIOLATION_TYPE)
async def process_violation_type(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=_safety_menu_keyboard())
        return

    await state.update_data(violation_type=message.text)
    await state.set_state(ReportViolationState.WAITING_FOR_LOCATION)

    await message.answer(
        "📍 <b>Где это происходит?</b>\n"
        "Укажите цех, участок или этаж.",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True)
    )

# --- 3. Место ---
@router.message(ReportViolationState.WAITING_FOR_LOCATION)
async def process_location(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=_safety_menu_keyboard())
        return

    await state.update_data(location=message.text)
    await state.set_state(ReportViolationState.WAITING_FOR_DESCRIPTION)

    await message.answer("📝 <b>Кратко опишите ситуацию:</b>")

# --- 4. Описание ---
@router.message(ReportViolationState.WAITING_FOR_DESCRIPTION)
async def process_description(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=_safety_menu_keyboard())
        return

    await state.update_data(description=message.text)
    await state.set_state(ReportViolationState.WAITING_FOR_PHOTO)

    await message.answer(
        "📸 <b>Приложите фото (если есть)</b>\n"
        "Или нажмите 'Пропустить'.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⏭ Пропустить")],
                [KeyboardButton(text="❌ Отмена")]
            ], resize_keyboard=True
        )
    )

# --- 5. Финал (Обработка фото или пропуска) ---
@router.message(ReportViolationState.WAITING_FOR_PHOTO)
async def finish_report(message: types.Message, state: FSMContext):
    # Проверка на отмену
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=_safety_menu_keyboard())
        return

    # Собираем данные (для красоты, никуда не шлем)
    data = await state.get_data()
    has_photo = bool(message.photo)

    # 1. Имитация бурной деятельности (Анимация)
    status_msg = await message.answer("⏳ <i>Формирование инцидента...</i>", parse_mode="HTML")
    await asyncio.sleep(1.0) # Пауза 1 сек для реализма
    await status_msg.edit_text("📡 <i>Отправка данных диспетчеру...</i>", parse_mode="HTML")
    await asyncio.sleep(1.0) # Пауза 1 сек
    await status_msg.delete()

    # 2. Генерируем фейковый номер заявки
    ticket_id = random.randint(1040, 9990)

    # 3. Финальное сообщение (как ты просил)
    final_text = (
        f"✅ <b>Нарушение зафиксировано!</b>\n"
        f"Тикет: <b>#INC-{ticket_id}</b>\n"
        f"──────────────────\n"
        f"📂 <b>Категория:</b> {data.get('violation_type')}\n"
        f"📍 <b>Место:</b> {data.get('location')}\n"
        f"📎 <b>Фотоматериалы:</b> {'Приложены' if has_photo else 'Отсутствуют'}\n\n"
        f"🛡 <b>Ваше обращение направлено в департамент охраны труда.</b>\n"
        f"Спасибо за бдительность!"
    )

    await message.answer(final_text, parse_mode="HTML", reply_markup=_safety_menu_keyboard())
    await state.clear()

def register_handlers(parent_router: Router):
    parent_router.include_router(router)