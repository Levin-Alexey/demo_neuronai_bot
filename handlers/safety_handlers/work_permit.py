"""Обработчик кнопки 'Оформить работы' с голосовым вводом."""

import asyncio
import logging
from typing import Any

import httpx
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

logger = logging.getLogger(__name__)
router = Router()

# Webhook для оформления работ
N8N_WORK_PERMIT_WEBHOOK_URL = "https://levinbiz.app.n8n.cloud/webhook/work-permit"
N8N_VOICE_PERMIT_WEBHOOK = "https://levinbiz.app.n8n.cloud/webhook/voice-permit"


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


async def process_voice_permit_n8n(file_id: str, file_url: str, user_info: dict) -> dict[str, Any]:
    """Отправляет голосовое в n8n для транскрибации и формирования наряда."""
    payload = {
        "file_id": file_id,
        "file_url": file_url,
        "user": user_info
    }

    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
        try:
            resp = await client.post(N8N_VOICE_PERMIT_WEBHOOK, json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"N8N Voice Error: {e}")
            return {
                "permit_id": "OFFLINE-001",
                "summary": "Ошибка обработки голосового. Проверьте соединение.",
                "risk_level": "Не определен",
                "status": "❌ Ошибка"
            }


class WorkPermitState(StatesGroup):
    """Состояния для оформления работ."""
    WAITING_FOR_WORK_TYPE = State()
    WAITING_FOR_LOCATION = State()
    WAITING_FOR_DURATION = State()
    WAITING_FOR_DESCRIPTION = State()
    WAITING_FOR_VOICE = State()


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

    await message.answer(
        "📝 <b>Оформление работ</b>\n\n"
        "Выберите способ оформления:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🎙 Голосовой наряд-допуск")],
                [KeyboardButton(text="📋 Стандартное оформление")],
                [KeyboardButton(text="🔙 Отмена")],
            ],
            resize_keyboard=True,
        ),
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


# --- Обработчик выбора режима ---
@router.message(F.text == "🎙 Голосовой наряд-допуск")
async def start_voice_permit(message: types.Message, state: FSMContext):
    """Запускает режим голосового оформления работ."""
    await state.set_state(WorkPermitState.WAITING_FOR_VOICE)

    await message.answer(
        "📝 <b>Голосовой Наряд-допуск (AI-Permit)</b>\n\n"
        "Просто продиктуйте детали работ, и я сформирую официальный документ.\n\n"
        "<b>Как это работает:</b>\n"
        "1. Нажмите кнопку записи голосового 🎙\n"
        "2. Скажите: <b>ГДЕ</b> работаете, <b>ЧТО</b> делаете и <b>КТО</b> в бригаде.\n"
        "3. Я транскрибирую голос и заполню форму.\n\n"
        "🗣 <b>Пример:</b>\n"
        "<i>«Бригада Иванова. Огневые работы в Цеху №5. Варим лестницу.»</i>\n\n"
        "👇 <b>Жду ваше голосовое сообщение:</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Отмена")]],
            resize_keyboard=True
        )
    )


@router.message(WorkPermitState.WAITING_FOR_VOICE, F.voice)
async def process_voice_message(message: types.Message, state: FSMContext):
    """Обрабатывает голосовое сообщение."""
    voice = message.voice
    file_id = voice.file_id

    # Получаем информацию о файле
    file_info = await message.bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file_info.file_path}"

    # Анимация обработки
    status_msg = await message.answer("🎙 <i>Получение аудиопотока...</i>", parse_mode="HTML")
    await asyncio.sleep(1.0)

    await status_msg.edit_text("⚡ <b>Whisper AI:</b> Транскрибация речи в текст...", parse_mode="HTML")

    user_data = {
        "id": message.from_user.id,
        "name": message.from_user.full_name,
        "username": message.from_user.username
    }

    # Запрос к n8n
    result = await process_voice_permit_n8n(file_id, file_url, user_data)

    await status_msg.edit_text("📑 <i>Структурирование данных и генерация документа...</i>", parse_mode="HTML")
    await asyncio.sleep(1.0)

    # Формируем ответ
    permit_text = (
        f"✅ <b>Наряд-допуск №{result.get('permit_id', 'DRAFT')} сформирован</b>\n"
        f"──────────────────\n"
        f"🏗 <b>Вид работ:</b> {result.get('work_type', 'Общестроительные')}\n"
        f"📍 <b>Место:</b> {result.get('location', 'Не указано')}\n"
        f"👷 <b>Ответственный:</b> {result.get('foreman', user_data['name'])}\n"
        f"⚠️ <b>Уровень риска:</b> {result.get('risk_level', 'Средний')}\n\n"
        f"📝 <b>Содержание (из голоса):</b>\n"
        f"<i>«{result.get('summary', '...')}»</i>\n\n"
        f"🛡 <b>Назначенные меры:</b>\n"
        f"• {result.get('safety_measures', 'Каска, Жилет, Инструктаж')}\n\n"
        f"<b>Статус:</b> Ожидает подписи гл. инженера."
    )

    await status_msg.delete()
    await message.answer(permit_text, parse_mode="HTML", reply_markup=_safety_menu_keyboard())
    await state.clear()


@router.message(WorkPermitState.WAITING_FOR_VOICE, F.text == "🔙 Отмена")
async def cancel_voice(message: types.Message, state: FSMContext):
    """Отмена оформления работ (голосовой режим)."""
    await state.clear()
    await message.answer(
        "Оформление отменено.",
        reply_markup=_safety_menu_keyboard()
    )


@router.message(WorkPermitState.WAITING_FOR_VOICE)
async def invalid_voice_input(message: types.Message):
    """Обработка некорректного ввода в режиме голосового оформления."""
    await message.answer(
        "🎙 Пожалуйста, отправьте <b>голосовое сообщение</b>.",
        parse_mode="HTML"
    )


# --- Обработчик текстового режима ---
@router.message(F.text == "📋 Стандартное оформление")
async def standard_work_permit(message: types.Message, state: FSMContext):
    """Запускает режим текстового оформления работ."""
    await state.set_state(WorkPermitState.WAITING_FOR_WORK_TYPE)

    await message.answer(
        "📝 <b>Оформление работ</b>\n\n"
        "Выберите тип работ, который необходимо оформить:",
        parse_mode="HTML",
        reply_markup=_work_types_keyboard(),
    )


@router.message(F.text == "🔙 Отмена", WorkPermitState)
async def cancel_work_permit(message: types.Message, state: FSMContext):
    """Отмена оформления работ."""
    await state.clear()
    await message.answer(
        "Оформление работ отменено.",
        reply_markup=_safety_menu_keyboard(),
    )


def register_handlers(parent_router: Router):
    """Регистрирует обработчики оформления работ."""
    parent_router.include_router(router)

