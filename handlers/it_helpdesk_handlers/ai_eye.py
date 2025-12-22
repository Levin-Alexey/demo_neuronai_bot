"""Обработчик кнопки 'AI-Глаз' с отправкой изображений/текста в n8n."""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import logging
from typing import Any
import httpx


logger = logging.getLogger(__name__)
router = Router()

# Webhook для Vision анализа
N8N_VISION_WEBHOOK_URL = "https://levinbiz.app.n8n.cloud/webhook/vision"


async def call_vision_n8n(payload: dict[str, Any]) -> dict[str, Any]:
    """Отправка данных на анализ в n8n (webhook /vision)."""

    try:
        print(f"\n{'='*60}")
        print(f"[VISION n8n REQUEST]")
        print(f"URL: {N8N_VISION_WEBHOOK_URL}")
        print(f"Payload: {payload}")

        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            response = await client.post(N8N_VISION_WEBHOOK_URL, json=payload)

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
        print(f"[VISION n8n ERROR]")
        print(f"URL: {N8N_VISION_WEBHOOK_URL}")
        print(f"Error: {type(e).__name__}: {e}")
        print(f"{'='*60}\n")
        raise


class AIEyeState(StatesGroup):
    """Состояния FSM для Vision анализа."""

    waiting_for_input = State()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены."""

    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


def get_it_helpdesk_keyboard() -> ReplyKeyboardMarkup:
    """Базовое меню IT Help Desk."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎫 Умный тикет")],
            [KeyboardButton(text="⚡ Мгновенные действия")],
            [KeyboardButton(text="🔍 AI-Глаз")],
            [KeyboardButton(text="🔌 Как подключиться")],
            [KeyboardButton(text="🔙 Назад в меню")],
        ],
        resize_keyboard=True,
    )


@router.message(F.text == "🔍 AI-Глаз")
async def ai_eye_handler(message: types.Message, state: FSMContext):
    """Активация режима Vision анализа."""

    await state.set_state(AIEyeState.waiting_for_input)
    await message.answer(
        "<b>Модуль компьютерного зрения (Vision) активирован</b>\n\n"
        "Описывать ошибку словами - долго. Переписывать коды сбоев вручную - риск ошибиться.\n"
        "Я использую технологию <b>Vision</b>, чтобы взглянуть на проблему вашими глазами.\n\n"
        "🚀 <b>Как это работает:</b>\n"
        "1. Вы присылаете скриншот ошибки, фото экрана или описываете сообщением в чат.\n"
        "2. Я сканирую изображение, распознаю текст, интерфейс и коды ошибок.\n"
        "3. Мгновенно сверяюсь с базой знаний и выдаю инструкцию по устранению.\n\n"
        "📉 <i>Я понимаю даже сложные логи, консольные ошибки и \"синие экраны смерти\".</i>\n\n"
        "👇 <b>Пришлите скриншот, фото или опишите ошибку прямо в этот чат.</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AIEyeState.waiting_for_input, F.text == "❌ Отмена")
async def cancel_ai_eye(message: types.Message, state: FSMContext) -> None:
    """Отмена режима Vision анализа."""

    await state.clear()
    await message.answer(
        "Анализ отменен.",
        reply_markup=get_it_helpdesk_keyboard(),
    )


@router.message(AIEyeState.waiting_for_input, F.photo)
async def handle_photo(message: types.Message, state: FSMContext) -> None:
    """Обработка фото/скриншота для анализа."""

    photo = message.photo[-1] if message.photo else None
    if not photo:
        await message.answer("⚠️ Не удалось получить изображение. Попробуйте еще раз.")
        return

    caption = (message.caption or "").strip()
    
    await message.answer(
        "📸 Изображение получено! Анализирую... Это может занять 10-15 секунд.",
        reply_markup=ReplyKeyboardRemove(),
    )

    await state.clear()

    try:
        payload = {
            "action": "vision_analyze",
            "telegram_id": message.from_user.id,
            "user_name": message.from_user.full_name or "",
            "content_type": "photo",
            "file_id": photo.file_id,
            "file_unique_id": photo.file_unique_id,
            "description": caption,
        }
        
        await call_vision_n8n(payload)
        
        await message.answer(
            "✅ Изображение отправлено на анализ. Я сообщу результат, как только он будет готов.",
            reply_markup=get_it_helpdesk_keyboard(),
        )
    except Exception as e:
        logger.error(f"Ошибка отправки изображения: {e}")
        await message.answer(
            f"❌ Ошибка отправки на анализ: {e}",
            reply_markup=get_it_helpdesk_keyboard(),
        )


@router.message(AIEyeState.waiting_for_input, F.text)
async def handle_text_description(message: types.Message, state: FSMContext) -> None:
    """Обработка текстового описания ошибки."""

    text_description = (message.text or "").strip()
    if not text_description:
        await message.answer("⚠️ Пожалуйста, опишите проблему или отправьте изображение.")
        return

    await message.answer(
        "📝 Описание получено! Анализирую... Это может занять 10-15 секунд.",
        reply_markup=ReplyKeyboardRemove(),
    )

    await state.clear()

    try:
        payload = {
            "action": "vision_analyze",
            "telegram_id": message.from_user.id,
            "user_name": message.from_user.full_name or "",
            "content_type": "text",
            "description": text_description,
        }
        
        await call_vision_n8n(payload)
        
        await message.answer(
            "✅ Описание отправлено на анализ. Я сообщу решение, как только оно будет готово.",
            reply_markup=get_it_helpdesk_keyboard(),
        )
    except Exception as e:
        logger.error(f"Ошибка отправки описания: {e}")
        await message.answer(
            f"❌ Ошибка отправки на анализ: {e}",
            reply_markup=get_it_helpdesk_keyboard(),
        )


@router.message(AIEyeState.waiting_for_input)
async def handle_other_content(message: types.Message) -> None:
    """Обработка других типов контента (документы, видео и т.д.)."""

    await message.answer(
        "⚠️ Пожалуйста, отправьте <b>фото/скриншот</b> или <b>текстовое описание</b> ошибки.",
        parse_mode="HTML",
    )


def register_handlers(parent_router: Router):
    parent_router.include_router(router)

