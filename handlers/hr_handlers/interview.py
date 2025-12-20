"""Обработчик режима 'Пройти собеседование' с интеграцией n8n.

Флоу:
1. Пользователь нажимает кнопку "🎭 Пройти собеседование"
2. Бот отправляет action=start в n8n, получает первый вопрос
3. Пользователь отвечает текстом или голосом
4. Бот отправляет action=answer в n8n, получает следующий вопрос или финал
5. После 3 вопросов — завершение с рекомендацией
"""

import os
import logging
import asyncio
from typing import Any

import httpx
from aiogram import F, Router, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

logger = logging.getLogger(__name__)

router = Router()

# ==================== Конфигурация ====================

N8N_WEBHOOK_URL = "https://levinbiz.app.n8n.cloud/webhook/interview"

HTTP_TIMEOUT = 60.0  # Whisper + LLM могут работать долго
N8N_RETRY_ATTEMPTS = 40  # ~120 сек при интервале 3 сек
N8N_RETRY_INTERVAL = 3.0  # сек


# ==================== Состояние сессий ====================
# Используем БД для надёжного хранилища (переживает перезапуски бота)

from models import (
    get_session,
    get_active_interview,
    start_interview,
    cancel_interview,
    save_answer_1,
    save_answer_2,
    save_answer_3_and_complete,
)


def is_in_interview(telegram_id: int) -> bool:
    """Проверить, проходит ли пользователь собеседование."""
    with get_session() as session:
        interview = get_active_interview(session, telegram_id)
        return interview is not None and interview.is_active


def start_session(telegram_id: int, first_question: str) -> None:
    """Отметить начало собеседования в БД."""
    with get_session() as session:
        start_interview(session, telegram_id, first_question)


def end_session(telegram_id: int) -> None:
    """Отметить завершение/отмену собеседования в БД."""
    with get_session() as session:
        cancel_interview(session, telegram_id)


# ==================== HTTP клиент для n8n ====================

async def _try_call_n8n_once(payload: dict[str, Any]) -> dict[str, Any]:
    """Один попыт вызова n8n."""
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, verify=False) as client:
            print(f"\n{'='*60}")
            print(f"[n8n REQUEST]")
            print(f"URL: {N8N_WEBHOOK_URL}")
            print(f"Payload: {payload}")

            response = await client.post(N8N_WEBHOOK_URL, json=payload)

            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            print(f"{'='*60}\n")

            response.raise_for_status()
            data = response.json()
            return data
    except httpx.HTTPStatusError as e:
        print(f"\n{'='*60}")
        print(f"[n8n ERROR - Status {e.response.status_code}]")
        print(f"URL: {N8N_WEBHOOK_URL}")
        print(f"Error: {e.response.text}")
        print(f"{'='*60}\n")

        if e.response.status_code == 404:
            # Webhook не зарегистрирован — нужно нажать Execute/Test в n8n
            raise  # Пробросим, чтобы retry логика могла обработать
        raise
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[n8n EXCEPTION]")
        print(f"Error: {type(e).__name__}: {e}")
        print(f"{'='*60}\n")
        logger.error(f"n8n call error: {e}")
        raise


async def call_n8n(payload: dict[str, Any]) -> dict[str, Any]:
    """Отправить запрос в n8n с автоматическим ретраем при 404.

    Returns:
        Ответ от n8n в формате:
        - При успехе: {"question": "...", "done": False} или {"result": "...", "done": True}
        - При ошибке: {"error": "..."}
    """
    last_error: Exception | None = None

    for attempt in range(N8N_RETRY_ATTEMPTS):
        try:
            logger.info(f"→ n8n (attempt {attempt + 1}): {payload.get('action')}")
            data = await _try_call_n8n_once(payload)
            logger.info(f"← n8n: success")
            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Webhook не готов — ждём и повторяем
                last_error = e
                if attempt < N8N_RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(N8N_RETRY_INTERVAL)
                    continue
            # Для других ошибок — не повторяем
            logger.error(f"n8n HTTP {e.response.status_code}: {e.response.text}")
            return {"error": f"Ошибка сервиса: {e.response.status_code}"}

        except httpx.TimeoutException:
            logger.error(f"n8n timeout")
            return {"error": "Сервис не отвечает, попробуйте позже"}

        except Exception as e:
            logger.error(f"n8n error: {e}")
            return {"error": "Не удалось связаться с сервисом"}

    # Все попытки исчерпаны, вернём ошибку 404
    logger.error(f"n8n: webhook not registered after {N8N_RETRY_ATTEMPTS} attempts")
    return {"error": "Webhook не зарегистрирован в n8n. Откройте workflow и нажмите 'Execute workflow' кнопку на canvas."}


# ==================== Клавиатуры ====================

def get_interview_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура во время собеседования."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить собеседование")]],
        resize_keyboard=True,
    )


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура HR-раздела (подставь свою)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎭 Пройти собеседование")],
            [KeyboardButton(text="◀️ Назад")],
        ],
        resize_keyboard=True,
    )


# ==================== Обработчики ====================

@router.message(F.text == "🎭 Пройти собеседование")
async def handle_start_interview(message: types.Message) -> None:
    """Запуск собеседования."""
    user = message.from_user
    if not user:
        return

    telegram_id = user.id

    # Если уже в процессе — напоминаем
    if is_in_interview(telegram_id):
        await message.answer(
            "⚠️ У вас уже идёт собеседование.\n"
            "Ответьте на вопрос или нажмите «❌ Отменить собеседование»."
        )
        return

    # Приветствие перед стартом
    await message.answer(
        "🧠 <b>Запускаю режим AI-интервью</b>\n\n"
        "Я активировала роль <b>HR Lead</b>. Сейчас я проведу с тобой собеседование.\n\n"
        "🔸 Я буду задавать вопросы.\n"
        "🔸 Вы отвечаете голосовыми или текстом.\n"
        "🔸 В конце я дам развернутый фидбек.\n\n"
        "🏁 <b>Готов начать? Жмите кнопку ниже!</b>",
        parse_mode="HTML",
        reply_markup=get_interview_keyboard(),
    )

    # Показываем статус
    status_msg = await message.answer(
        "⏳ <b>Подготавливаю собеседование...</b>\n\n"
        "Если это займёт больше 10 секунд, значит в n8n нужно нажать кнопку 'Execute workflow'.\n"
        "Пожалуйста, подождите...",
        parse_mode="HTML"
    )

    # Запрос в n8n
    data = await call_n8n({
        "action": "start",
        "telegram_id": telegram_id,
        "chat_id": message.chat.id,
        "username": user.username or "",
        "full_name": user.full_name or "",
    })

    # Удаляем статус
    try:
        await status_msg.delete()
    except Exception:
        pass

    # Проверяем ошибку
    if "error" in data:
        await message.answer(
            f"❌ {data['error']}\n\n"
            "<b>Что делать:</b>\n"
            "1. Откройте workflow в n8n\n"
            "2. Нажмите кнопку 'Execute workflow' на canvas\n"
            "3. Повторите попытку в Telegram"
        )
        return

    # Успех — начинаем сессию в БД
    question = data.get("question", "Расскажите о себе и вашем опыте в продажах.")
    start_session(telegram_id, question)

    await message.answer(
        "🎤 <b>Собеседование на позицию «Менеджер по продажам»</b>\n\n"
        f"<b>Вопрос 1 из 3:</b>\n{question}\n\n"
        "💬 Ответьте текстом или 🎙 голосовым сообщением.",
        parse_mode="HTML",
        reply_markup=get_interview_keyboard(),
    )


@router.message(F.text == "❌ Отменить собеседование")
async def handle_cancel_interview(message: types.Message) -> None:
    """Отмена собеседования."""
    user = message.from_user
    if not user:
        return

    telegram_id = user.id

    if not is_in_interview(telegram_id):
        await message.answer("У вас нет активного собеседования.")
        return

    # Уведомляем n8n
    await call_n8n({
        "action": "cancel",
        "telegram_id": telegram_id,
    })

    end_session(telegram_id)

    await message.answer(
        "🚫 Собеседование отменено.\n"
        "Вы можете начать заново в любое время.",
        reply_markup=get_main_keyboard(),
    )


@router.message(F.voice)
async def handle_voice_answer(message: types.Message) -> None:
    """Голосовой ответ на вопрос собеседования."""
    user = message.from_user
    if not user:
        return

    telegram_id = user.id

    # Проверяем, что пользователь в режиме собеседования
    if not is_in_interview(telegram_id):
        return  # Игнорируем голосовые вне собеседования

    voice = message.voice
    if not voice:
        return

    # Показываем статус (Whisper + LLM занимают время)
    status_msg = await message.answer("🎙 Обрабатываю голосовое сообщение...")

    # Запрос в n8n
    data = await call_n8n({
        "action": "answer",
        "telegram_id": telegram_id,
        "chat_id": message.chat.id,
        "type": "voice",
        "voice_file_id": voice.file_id,
        "duration": voice.duration,
    })

    # Удаляем статус
    try:
        await status_msg.delete()
    except Exception:
        pass

    # Обрабатываем ответ
    await _process_n8n_response(message, telegram_id, data)


@router.message(F.text)
async def handle_text_answer(message: types.Message) -> None:
    """Текстовый ответ на вопрос собеседования."""
    user = message.from_user
    if not user:
        return

    telegram_id = user.id
    text = (message.text or "").strip()

    # Не отправляем в n8n кнопки меню
    menu_buttons = {
        "📄 Анализ резюме (CV Scan)",
        "🔥 Быстрый подбор",
        "⚙️ Информация для HR",
        "🔙 Назад в меню",
        "🤝 HR и найм",
        "👷‍♂️ Охрана труда",
        "🛠 IT HelpDesk",
        "🧠 База Знаний",
        "💰 AI-Менеджер",
        "🎭 Пройти собеседование",
        "❌ Отмена",
        "◀️ Назад",
    }
    if text in menu_buttons:
        return

    # Проверяем, что пользователь в режиме собеседования
    if not is_in_interview(telegram_id):
        return  # Игнорируем текст вне собеседования

    # Игнорируем пустые и служебные сообщения
    if not text or text.startswith("/"):
        return

    # Показываем статус
    status_msg = await message.answer("💭 Анализирую ответ...")

    # Запрос в n8n
    data = await call_n8n({
        "action": "answer",
        "telegram_id": telegram_id,
        "chat_id": message.chat.id,
        "type": "text",
        "text": text,
    })

    # Удаляем статус
    try:
        await status_msg.delete()
    except Exception:
        pass

    # Обрабатываем ответ
    await _process_n8n_response(message, telegram_id, data)


async def _process_n8n_response(
    message: types.Message,
    telegram_id: int,
    data: dict[str, Any],
) -> None:
    """Обработка ответа от n8n после ответа кандидата."""

    # Ошибка
    if "error" in data:
        await message.answer(f"❌ {data['error']}")
        return

    # Проверяем, завершено ли собеседование
    is_done = data.get("done", False)
    stage = data.get("stage", 0)  # текущий этап после сохранения
    answer_text = data.get("answer", "")  # текст ответа (расшифрованный через Whisper если голос)
    voice_file_id = data.get("voice_file_id")  # ID голосового файла если был

    if is_done:
        # Финал — сохраняем последний ответ и завершаем
        result = data.get("result", "")
        hr_summary = data.get("hr_recommendation", {})

        with get_session() as session:
            try:
                # Сохраняем 3-й ответ и завершаем собеседование
                save_answer_3_and_complete(
                    session,
                    telegram_id,
                    answer=answer_text,
                    hr_recommendation=hr_summary,
                    voice_file_id=voice_file_id,
                )
            except Exception as e:
                print(f"Error saving final answer to DB: {e}")

        # Завершаем сессию в любом случае
        end_session(telegram_id)

        await message.answer(
            "✅ <b>Собеседование завершено!</b>\n\n"
            "Спасибо за уделённое время! 🙏",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(),
        )
    else:
        # Следующий вопрос - сохраняем ответ и вопрос
        question = data.get("question", "Продолжайте, пожалуйста.")
        question_num = stage + 1  # stage 0 = вопрос 1, stage 1 = вопрос 2, stage 2 = вопрос 3

        # Сохраняем в БД в зависимости от этапа
        with get_session() as session:
            try:
                # ВАЖНО: Мы ориентируемся на ответ n8n, а не на базу, чтобы избежать гонки
                if stage == 1:
                    # n8n перевел нас на 1 этап -> значит мы сохраняем ответ на 1 вопрос
                    save_answer_1(session, telegram_id, answer_text, question, voice_file_id)
                elif stage == 2:
                    # n8n перевел нас на 2 этап -> значит мы сохраняем ответ на 2 вопрос
                    save_answer_2(session, telegram_id, answer_text, question, voice_file_id)
            except Exception as e:
                print(f"Error saving answer to DB: {e}")

        await message.answer(
            f"<b>Вопрос {question_num} из 3:</b>\n{question}\n\n"
            "💬 Ответьте текстом или 🎙 голосовым сообщением.",
            parse_mode="HTML",
            reply_markup=get_interview_keyboard(),
        )


# ==================== Регистрация ====================

def register_interview_handlers(parent_router: Router) -> None:
    """Зарегистрировать обработчики собеседования в основном роутере."""
    parent_router.include_router(router)

# Совместимость с существующим кодом (handlers/hr.py ожидает register_handlers)
def register_handlers(parent_router: Router) -> None:
    register_interview_handlers(parent_router)
