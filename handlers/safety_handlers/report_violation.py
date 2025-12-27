"""Обработчик кнопки 'Сообщить о нарушении'."""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
from typing import Any
import httpx


logger = logging.getLogger(__name__)
router = Router()

# Webhook для сообщения о нарушениях
N8N_REPORT_VIOLATION_WEBHOOK_URL = "https://levinbiz.app.n8n.cloud/webhook/report-violation"


async def call_report_violation_n8n(payload: dict[str, Any]) -> dict[str, Any]:
    """Отправка данных о нарушении в n8n."""

    try:
        print(f"\n{'='*60}")
        print(f"[REPORT VIOLATION n8n REQUEST]")
        print(f"URL: {N8N_REPORT_VIOLATION_WEBHOOK_URL}")
        print(f"Payload: {payload}")

        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            response = await client.post(N8N_REPORT_VIOLATION_WEBHOOK_URL, json=payload)

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
        print(f"[REPORT VIOLATION n8n ERROR]")
        print(f"URL: {N8N_REPORT_VIOLATION_WEBHOOK_URL}")
        print(f"Error: {type(e).__name__}: {e}")
        print(f"{'='*60}\n")
        raise


class ReportViolationState(StatesGroup):
    """Состояния для сообщения о нарушении."""
    WAITING_FOR_VIOLATION_TYPE = State()
    WAITING_FOR_LOCATION = State()
    WAITING_FOR_DESCRIPTION = State()
    WAITING_FOR_PHOTO = State()


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


def _violation_types_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру с типами нарушений."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚠️ Нарушение техники безопасности")],
            [KeyboardButton(text="🦺 Отсутствие СИЗ")],
            [KeyboardButton(text="🔥 Пожарная опасность")],
            [KeyboardButton(text="⚡ Электробезопасность")],
            [KeyboardButton(text="🏗 Небезопасное оборудование")],
            [KeyboardButton(text="📋 Другое")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


@router.message(F.text == "🆘 Сообщить о нарушении")
async def report_violation_handler(message: types.Message, state: FSMContext):
    """Запускает процесс сообщения о нарушении."""

    await state.set_state(ReportViolationState.WAITING_FOR_VIOLATION_TYPE)

    await message.answer(
        "🆘 <b>Сообщение о нарушении</b>\n\n"
        "Ваша бдительность помогает сделать рабочее место безопаснее!\n\n"
        "Выберите тип нарушения:",
        parse_mode="HTML",
        reply_markup=_violation_types_keyboard(),
    )


@router.message(ReportViolationState.WAITING_FOR_VIOLATION_TYPE)
async def process_violation_type(message: types.Message, state: FSMContext):
    """Обрабатывает выбор типа нарушения."""

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Сообщение о нарушении отменено.",
            reply_markup=_safety_menu_keyboard(),
        )
        return

    violation_types = {
        "⚠️ Нарушение техники безопасности": "safety_violation",
        "🦺 Отсутствие СИЗ": "no_ppe",
        "🔥 Пожарная опасность": "fire_hazard",
        "⚡ Электробезопасность": "electrical_safety",
        "🏗 Небезопасное оборудование": "unsafe_equipment",
        "📋 Другое": "other",
    }

    if message.text not in violation_types:
        await message.answer("❌ Пожалуйста, выберите тип нарушения из предложенных вариантов.")
        return

    await state.update_data(violation_type=violation_types[message.text], violation_type_text=message.text)
    await state.set_state(ReportViolationState.WAITING_FOR_LOCATION)

    await message.answer(
        "📍 <b>Укажите место нарушения</b>\n\n"
        "Например: 'Цех №2, зона погрузки' или 'Складское помещение А'",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True,
        ),
    )


@router.message(ReportViolationState.WAITING_FOR_LOCATION)
async def process_violation_location(message: types.Message, state: FSMContext):
    """Обрабатывает указание места нарушения."""

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Сообщение о нарушении отменено.",
            reply_markup=_safety_menu_keyboard(),
        )
        return

    await state.update_data(location=message.text)
    await state.set_state(ReportViolationState.WAITING_FOR_DESCRIPTION)

    await message.answer(
        "📝 <b>Опишите нарушение подробно</b>\n\n"
        "Укажите, что именно нарушается, кто вовлечен (если известно), и какая угроза существует.",
        parse_mode="HTML",
    )


@router.message(ReportViolationState.WAITING_FOR_DESCRIPTION)
async def process_violation_description(message: types.Message, state: FSMContext):
    """Обрабатывает описание нарушения."""

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Сообщение о нарушении отменено.",
            reply_markup=_safety_menu_keyboard(),
        )
        return

    await state.update_data(description=message.text)
    await state.set_state(ReportViolationState.WAITING_FOR_PHOTO)

    await message.answer(
        "📸 <b>Приложите фото нарушения (опционально)</b>\n\n"
        "Отправьте фотографию для более точной оценки ситуации, или нажмите 'Пропустить'.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⏭ Пропустить")],
                [KeyboardButton(text="❌ Отмена")],
            ],
            resize_keyboard=True,
        ),
    )


@router.message(ReportViolationState.WAITING_FOR_PHOTO, F.photo)
async def process_violation_photo(message: types.Message, state: FSMContext):
    """Обрабатывает фото нарушения и отправляет отчет."""

    photo = message.photo[-1]
    file_id = photo.file_id

    # Получаем URL фото
    bot = message.bot
    file = await bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

    await state.update_data(photo_url=file_url, photo_file_id=file_id)

    await send_violation_report(message, state)


@router.message(ReportViolationState.WAITING_FOR_PHOTO, F.text == "⏭ Пропустить")
async def skip_violation_photo(message: types.Message, state: FSMContext):
    """Пропускает добавление фото и отправляет отчет."""

    await send_violation_report(message, state)


@router.message(ReportViolationState.WAITING_FOR_PHOTO, F.text == "❌ Отмена")
async def cancel_violation_report(message: types.Message, state: FSMContext):
    """Отменяет сообщение о нарушении."""

    await state.clear()
    await message.answer(
        "Сообщение о нарушении отменено.",
        reply_markup=_safety_menu_keyboard(),
    )


@router.message(ReportViolationState.WAITING_FOR_PHOTO)
async def violation_photo_invalid_input(message: types.Message):
    """Обрабатывает неверный ввод при ожидании фото."""

    await message.answer(
        "❌ Пожалуйста, отправьте фотографию, нажмите 'Пропустить' или 'Отмена'.",
    )


async def send_violation_report(message: types.Message, state: FSMContext):
    """Отправляет отчет о нарушении в n8n."""

    data = await state.get_data()

    await message.answer("⏳ Отправляю сообщение о нарушении...")

    try:
        # Подготавливаем данные для отправки в n8n
        payload = {
            "telegram_id": message.from_user.id,
            "username": message.from_user.username or "unknown",
            "full_name": message.from_user.full_name,
            "violation_type": data.get("violation_type"),
            "violation_type_text": data.get("violation_type_text"),
            "location": data.get("location"),
            "description": data.get("description"),
            "photo_url": data.get("photo_url", ""),
            "photo_file_id": data.get("photo_file_id", ""),
        }

        # Отправляем в n8n
        response = await call_report_violation_n8n(payload)

        # Получаем результат
        report_number = response.get("report_number", "N/A")
        result_text = response.get("message", "Ваше сообщение принято и будет рассмотрено службой охраны труда.")

        await message.answer(
            f"✅ <b>Сообщение о нарушении отправлено!</b>\n\n"
            f"📋 Номер обращения: <b>{report_number}</b>\n\n"
            f"{result_text}\n\n"
            f"Служба охраны труда свяжется с вами в ближайшее время.\n\n"
            f"<b>Детали обращения:</b>\n"
            f"• Тип: {data.get('violation_type_text')}\n"
            f"• Место: {data.get('location')}\n"
            f"• Описание: {data.get('description')}\n"
            f"• Фото: {'Приложено' if data.get('photo_url') else 'Не приложено'}",
            parse_mode="HTML",
            reply_markup=_safety_menu_keyboard(),
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Error sending violation report: {e}")
        await message.answer(
            "❌ Произошла ошибка при отправке сообщения. Попробуйте еще раз или обратитесь к администратору.",
            reply_markup=_safety_menu_keyboard(),
        )
        await state.clear()


def register_handlers(parent_router: Router):
    """Регистрирует обработчики сообщения о нарушении."""
    parent_router.include_router(router)

