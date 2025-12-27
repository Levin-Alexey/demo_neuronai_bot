"""Обработчик кнопки 'Получить допуск (Фото-контроль)' с отправкой изображений в n8n."""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
from typing import Any
import httpx


logger = logging.getLogger(__name__)
router = Router()

# Webhook для анализа фото допуска
N8N_PHOTO_CONTROL_WEBHOOK_URL = "https://levinbiz.app.n8n.cloud/webhook/photo-control"


async def call_photo_control_n8n(payload: dict[str, Any]) -> dict[str, Any]:
    """Отправка данных на анализ фото допуска в n8n."""

    try:
        print(f"\n{'='*60}")
        print(f"[PHOTO CONTROL n8n REQUEST]")
        print(f"URL: {N8N_PHOTO_CONTROL_WEBHOOK_URL}")
        print(f"Payload: {payload}")

        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            response = await client.post(N8N_PHOTO_CONTROL_WEBHOOK_URL, json=payload)

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
        print(f"[PHOTO CONTROL n8n ERROR]")
        print(f"URL: {N8N_PHOTO_CONTROL_WEBHOOK_URL}")
        print(f"Error: {type(e).__name__}: {e}")
        print(f"{'='*60}\n")
        raise


class PhotoControlState(StatesGroup):
    """Состояния для фото-контроля допуска."""
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


@router.message(F.text == "📸 Получить допуск")
async def photo_control_handler(message: types.Message, state: FSMContext):
    """Запускает процесс получения допуска через фото-контроль."""

    await state.set_state(PhotoControlState.WAITING_FOR_PHOTO)

    await message.answer(
        "📸 <b>Фото-контроль для получения допуска</b>\n\n"
        "Пожалуйста, отправьте фотографию:\n"
        "• Себя в средствах защиты\n"
        "• Или зону работ\n"
        "• Или документы допуска\n\n"
        "Я проанализирую изображение и выдам допуск или укажу на нарушения.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True,
        ),
    )


@router.message(PhotoControlState.WAITING_FOR_PHOTO, F.photo)
async def process_photo_control(message: types.Message, state: FSMContext):
    """Обрабатывает полученное фото для контроля допуска."""

    photo = message.photo[-1]  # Берем самое большое фото
    file_id = photo.file_id

    await message.answer("⏳ Анализирую фотографию, подождите...")

    try:
        # Получаем информацию о файле
        bot = message.bot
        file = await bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

        # Подготавливаем данные для отправки в n8n
        payload = {
            "telegram_id": message.from_user.id,
            "username": message.from_user.username or "unknown",
            "file_url": file_url,
            "file_id": file_id,
            "caption": message.caption or "",
        }

        # Отправляем в n8n
        response = await call_photo_control_n8n(payload)

        # Получаем результат анализа
        result_text = response.get("analysis", "Анализ выполнен, но результат не получен.")

        await message.answer(
            f"📋 <b>Результат проверки:</b>\n\n{result_text}",
            parse_mode="HTML",
            reply_markup=_safety_menu_keyboard(),
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Error processing photo control: {e}")
        await message.answer(
            "❌ Произошла ошибка при анализе фотографии. Попробуйте еще раз.",
            reply_markup=_safety_menu_keyboard(),
        )
        await state.clear()


@router.message(PhotoControlState.WAITING_FOR_PHOTO, F.text == "❌ Отмена")
async def cancel_photo_control(message: types.Message, state: FSMContext):
    """Отменяет процесс фото-контроля."""

    await state.clear()
    await message.answer(
        "Фото-контроль отменен. Возвращаю в меню Охраны труда.",
        reply_markup=_safety_menu_keyboard(),
    )


@router.message(PhotoControlState.WAITING_FOR_PHOTO)
async def photo_control_invalid_input(message: types.Message):
    """Обрабатывает неверный ввод при ожидании фото."""

    await message.answer(
        "❌ Пожалуйста, отправьте фотографию или нажмите '❌ Отмена'.",
    )


def register_handlers(parent_router: Router):
    """Регистрирует обработчики фото-контроля."""
    parent_router.include_router(router)

