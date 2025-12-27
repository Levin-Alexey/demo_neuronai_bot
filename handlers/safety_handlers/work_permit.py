"""Обработчик кнопки 'Оформить работы'."""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
from typing import Any
import httpx


logger = logging.getLogger(__name__)
router = Router()

# Webhook для оформления работ
N8N_WORK_PERMIT_WEBHOOK_URL = "https://levinbiz.app.n8n.cloud/webhook/work-permit"


async def call_work_permit_n8n(payload: dict[str, Any]) -> dict[str, Any]:
    """Отправка данных для оформления работ в n8n."""

    try:
        print(f"\n{'='*60}")
        print(f"[WORK PERMIT n8n REQUEST]")
        print(f"URL: {N8N_WORK_PERMIT_WEBHOOK_URL}")
        print(f"Payload: {payload}")

        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            response = await client.post(N8N_WORK_PERMIT_WEBHOOK_URL, json=payload)

            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            print(f"{'='*60}\n")

            response.raise_for_status()
            if response.content:
                try:
                    return response.json()
                except Exception:
                    return {"raw": response.text}
            return {}
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[WORK PERMIT n8n ERROR]")
        print(f"URL: {N8N_WORK_PERMIT_WEBHOOK_URL}")
        print(f"Error: {type(e).__name__}: {e}")
        print(f"{'='*60}\n")
        raise


class WorkPermitState(StatesGroup):
    """Состояния для оформления работ."""
    WAITING_FOR_WORK_TYPE = State()
    WAITING_FOR_LOCATION = State()
    WAITING_FOR_DURATION = State()
    WAITING_FOR_DESCRIPTION = State()


def _safety_menu_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру меню Охраны труда."""
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


def _work_types_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру с типами работ."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔧 Ремонтные работы")],
            [KeyboardButton(text="⚡ Электротехнические работы")],
            [KeyboardButton(text="🔥 Огневые работы")],
            [KeyboardButton(text="⬆️ Высотные работы")],
            [KeyboardButton(text="🏗 Строительные работы")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


@router.message(F.text == "📝 Оформить работы")
async def work_permit_handler(message: types.Message, state: FSMContext):
    """Запускает процесс оформления работ."""

    await state.set_state(WorkPermitState.WAITING_FOR_WORK_TYPE)

    await message.answer(
        "📝 <b>Оформление работ</b>\n\n"
        "Выберите тип работ, который необходимо оформить:",
        parse_mode="HTML",
        reply_markup=_work_types_keyboard(),
    )


@router.message(WorkPermitState.WAITING_FOR_WORK_TYPE)
async def process_work_type(message: types.Message, state: FSMContext):
    """Обрабатывает выбор типа работ."""

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Оформление работ отменено.",
            reply_markup=_safety_menu_keyboard(),
        )
        return

    work_types = {
        "🔧 Ремонтные работы": "repair",
        "⚡ Электротехнические работы": "electrical",
        "🔥 Огневые работы": "fire",
        "⬆️ Высотные работы": "height",
        "🏗 Строительные работы": "construction",
    }

    if message.text not in work_types:
        await message.answer("❌ Пожалуйста, выберите тип работ из предложенных вариантов.")
        return

    await state.update_data(work_type=work_types[message.text], work_type_text=message.text)
    await state.set_state(WorkPermitState.WAITING_FOR_LOCATION)

    await message.answer(
        "📍 <b>Укажите место проведения работ</b>\n\n"
        "Например: 'Цех №2, участок сборки' или 'Офисное здание, 3 этаж'",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True,
        ),
    )


@router.message(WorkPermitState.WAITING_FOR_LOCATION)
async def process_location(message: types.Message, state: FSMContext):
    """Обрабатывает указание места проведения работ."""

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Оформление работ отменено.",
            reply_markup=_safety_menu_keyboard(),
        )
        return

    await state.update_data(location=message.text)
    await state.set_state(WorkPermitState.WAITING_FOR_DURATION)

    await message.answer(
        "⏱ <b>Укажите планируемую длительность работ</b>\n\n"
        "Например: '2 часа', '1 день', '3 дня'",
        parse_mode="HTML",
    )


@router.message(WorkPermitState.WAITING_FOR_DURATION)
async def process_duration(message: types.Message, state: FSMContext):
    """Обрабатывает указание длительности работ."""

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Оформление работ отменено.",
            reply_markup=_safety_menu_keyboard(),
        )
        return

    await state.update_data(duration=message.text)
    await state.set_state(WorkPermitState.WAITING_FOR_DESCRIPTION)

    await message.answer(
        "📋 <b>Опишите суть работ и необходимые меры безопасности</b>\n\n"
        "Например: 'Замена электропроводки. Требуется отключение питания и СИЗ'",
        parse_mode="HTML",
    )


@router.message(WorkPermitState.WAITING_FOR_DESCRIPTION)
async def process_description(message: types.Message, state: FSMContext):
    """Обрабатывает описание работ и отправляет заявку."""

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Оформление работ отменено.",
            reply_markup=_safety_menu_keyboard(),
        )
        return

    data = await state.get_data()

    await message.answer("⏳ Оформляю документы, подождите...")

    try:
        # Подготавливаем данные для отправки в n8n
        payload = {
            "telegram_id": message.from_user.id,
            "username": message.from_user.username or "unknown",
            "full_name": message.from_user.full_name,
            "work_type": data.get("work_type"),
            "work_type_text": data.get("work_type_text"),
            "location": data.get("location"),
            "duration": data.get("duration"),
            "description": message.text,
        }

        # Отправляем в n8n
        response = await call_work_permit_n8n(payload)

        # Получаем результат
        permit_number = response.get("permit_number", "N/A")
        result_text = response.get("message", "Заявка на оформление работ принята.")

        await message.answer(
            f"✅ <b>Работы оформлены!</b>\n\n"
            f"📋 Номер наряда-допуска: <b>{permit_number}</b>\n\n"
            f"{result_text}\n\n"
            f"<b>Детали заявки:</b>\n"
            f"• Тип работ: {data.get('work_type_text')}\n"
            f"• Место: {data.get('location')}\n"
            f"• Длительность: {data.get('duration')}\n"
            f"• Описание: {message.text}",
            parse_mode="HTML",
            reply_markup=_safety_menu_keyboard(),
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Error processing work permit: {e}")
        await message.answer(
            "❌ Произошла ошибка при оформлении работ. Попробуйте еще раз или обратитесь к администратору.",
            reply_markup=_safety_menu_keyboard(),
        )
        await state.clear()


def register_handlers(parent_router: Router):
    """Регистрирует обработчики оформления работ."""
    parent_router.include_router(router)

