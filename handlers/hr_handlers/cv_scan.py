"""Обработчик кнопки 'Анализ резюме (CV Scan)' с загрузкой файла и отправкой в n8n."""

from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import os
import logging
from typing import Any
import httpx


logger = logging.getLogger(__name__)
router = Router()

# Жёстко задаём вебхук CV Scan
N8N_CV_SCAN_WEBHOOK_URL = "https://levinbiz.app.n8n.cloud/webhook-test/scan"


async def call_cv_scan_n8n(payload: dict[str, Any]) -> dict[str, Any]:
    """Отправка файла на анализ в n8n (webhook /scan)."""

    try:
        print(f"\n{'='*60}")
        print(f"[CV_SCAN n8n REQUEST]")
        print(f"URL: {N8N_CV_SCAN_WEBHOOK_URL}")
        print(f"Payload: {payload}")

        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            response = await client.post(N8N_CV_SCAN_WEBHOOK_URL, json=payload)

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
        print(f"[CV_SCAN n8n ERROR]")
        print(f"URL: {N8N_CV_SCAN_WEBHOOK_URL}")
        print(f"Error: {type(e).__name__}: {e}")
        print(f"{'='*60}\n")
        raise


class CVScanState(StatesGroup):
    """Состояния FSM для загрузки резюме."""

    waiting_for_file = State()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены для режима загрузки."""

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


@router.message(F.text == "📄 Анализ резюме (CV Scan)")
async def start_cv_scan(message: types.Message, state: FSMContext) -> None:
    """Запуск режима анализа резюме."""

    await state.set_state(CVScanState.waiting_for_file)
    await message.answer(
        "📄 <b>Режим проверки резюме</b>\n\n"
        "Пожалуйста, отправьте файл резюме (PDF или DOCX).\n"
        "Я проанализирую его и дам оценку.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(CVScanState.waiting_for_file, F.text == "❌ Отмена")
async def cancel_cv_scan(message: types.Message, state: FSMContext) -> None:
    """Отмена загрузки резюме."""

    await state.clear()
    await message.answer(
        "Сканирование отменено.",
        reply_markup=get_hr_keyboard(),
    )


@router.message(CVScanState.waiting_for_file, F.document)
async def handle_cv_file(message: types.Message, state: FSMContext) -> None:
    """Обрабатываем загруженный файл и отправляем его в n8n."""

    document = message.document
    if not document:
        await message.answer("⚠️ Пожалуйста, пришлите файл в формате PDF или Word (DOCX).")
        return

    file_name = (document.file_name or "").lower()
    if not (file_name.endswith(".pdf") or file_name.endswith(".doc") or file_name.endswith(".docx")):
        await message.answer("⚠️ Пожалуйста, пришлите файл в формате PDF или Word (DOCX).")
        return

    await message.answer(
        "📥 Файл получен! Отправляю на анализ к ИИ... Это может занять 10-15 секунд.",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Сбрасываем состояние, чтобы не ждать второй файл
    await state.clear()

    try:
        await call_cv_scan_n8n(
            {
                "action": "cv_scan",
                "telegram_id": message.from_user.id,
                "user_name": message.from_user.full_name or "",
                "file_id": document.file_id,
                "file_name": document.file_name or "",
                "mime_type": document.mime_type or "",
            }
        )
        # Сообщение можно расширить, когда n8n начнет возвращать результат сразу
        await message.answer(
            "✅ Резюме отправлено на анализ. Я сообщу результат, как только он будет готов.",
            reply_markup=get_hr_keyboard(),
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка отправки: {e}",
            reply_markup=get_hr_keyboard(),
        )


@router.message(CVScanState.waiting_for_file)
async def warning_not_file(message: types.Message) -> None:
    """Подсказываем, что нужен файл, если пользователь отправил что-то другое."""

    await message.answer(
        "Пожалуйста, прикрепите именно <b>файл</b> (как документ), а не картинку или текст.",
        parse_mode="HTML",
    )


def register_handlers(main_router: Router) -> None:
    """Регистрация обработчиков анализа резюме."""

    main_router.include_router(router)
