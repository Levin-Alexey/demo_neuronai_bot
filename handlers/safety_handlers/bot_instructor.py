"""Обработчик кнопки 'Бот-Инструктор'."""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
from typing import Any
import httpx


logger = logging.getLogger(__name__)
router = Router()

# Webhook для бота-инструктора
N8N_BOT_INSTRUCTOR_WEBHOOK_URL = "https://levinbiz.app.n8n.cloud/webhook/bot-instructor"


async def call_bot_instructor_n8n(payload: dict[str, Any]) -> dict[str, Any]:
    """Отправка запроса к боту-инструктору в n8n."""

    try:
        print(f"\n{'='*60}")
        print(f"[BOT INSTRUCTOR n8n REQUEST]")
        print(f"URL: {N8N_BOT_INSTRUCTOR_WEBHOOK_URL}")
        print(f"Payload: {payload}")

        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            response = await client.post(N8N_BOT_INSTRUCTOR_WEBHOOK_URL, json=payload)

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
        print(f"[BOT INSTRUCTOR n8n ERROR]")
        print(f"URL: {N8N_BOT_INSTRUCTOR_WEBHOOK_URL}")
        print(f"Error: {type(e).__name__}: {e}")
        print(f"{'='*60}\n")
        raise


class BotInstructorState(StatesGroup):
    """Состояния для бота-инструктора."""
    WAITING_FOR_TOPIC = State()
    IN_CONVERSATION = State()


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


def _instructor_topics_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру с темами для инструктажа."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🦺 СИЗ и их применение")],
            [KeyboardButton(text="🔥 Пожарная безопасность")],
            [KeyboardButton(text="⚡ Электробезопасность")],
            [KeyboardButton(text="⬆️ Работа на высоте")],
            [KeyboardButton(text="🏗 Работа с оборудованием")],
            [KeyboardButton(text="🚨 Действия при ЧС")],
            [KeyboardButton(text="💬 Свой вопрос")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


@router.message(F.text == "🧠 Бот-Инструктор")
async def bot_instructor_handler(message: types.Message, state: FSMContext):
    """Запускает режим бота-инструктора."""

    await state.set_state(BotInstructorState.WAITING_FOR_TOPIC)

    await message.answer(
        "🧠 <b>Бот-Инструктор по охране труда</b>\n\n"
        "Я помогу вам разобраться в вопросах безопасности труда, проведу инструктаж и отвечу на ваши вопросы.\n\n"
        "Выберите тему или задайте свой вопрос:",
        parse_mode="HTML",
        reply_markup=_instructor_topics_keyboard(),
    )


@router.message(BotInstructorState.WAITING_FOR_TOPIC)
async def process_instructor_topic(message: types.Message, state: FSMContext):
    """Обрабатывает выбор темы инструктажа."""

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Бот-Инструктор завершил работу.",
            reply_markup=_safety_menu_keyboard(),
        )
        return

    topics = {
        "🦺 СИЗ и их применение": "ppe",
        "🔥 Пожарная безопасность": "fire_safety",
        "⚡ Электробезопасность": "electrical_safety",
        "⬆️ Работа на высоте": "work_at_height",
        "🏗 Работа с оборудованием": "equipment",
        "🚨 Действия при ЧС": "emergency",
        "💬 Свой вопрос": "custom",
    }

    # Если выбрана готовая тема
    if message.text in topics:
        topic_code = topics[message.text]

        if topic_code == "custom":
            await message.answer(
                "💬 <b>Задайте свой вопрос</b>\n\n"
                "Напишите ваш вопрос по охране труда, и я постараюсь дать подробный ответ.",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="❌ Отмена")]],
                    resize_keyboard=True,
                ),
            )
            await state.set_state(BotInstructorState.IN_CONVERSATION)
            await state.update_data(topic="custom", topic_text=message.text)
            return

        await state.update_data(topic=topic_code, topic_text=message.text)
        await process_instructor_query(message, state, message.text)

    # Если это свободный вопрос
    else:
        await state.update_data(topic="custom", topic_text="Свой вопрос")
        await process_instructor_query(message, state, message.text)


async def process_instructor_query(message: types.Message, state: FSMContext, query: str):
    """Обрабатывает запрос к боту-инструктору."""

    await message.answer("🤔 Анализирую вопрос и готовлю ответ...")

    data = await state.get_data()

    try:
        # Подготавливаем данные для отправки в n8n
        payload = {
            "telegram_id": message.from_user.id,
            "username": message.from_user.username or "unknown",
            "full_name": message.from_user.full_name,
            "topic": data.get("topic"),
            "topic_text": data.get("topic_text"),
            "query": query,
            "action": "query",
        }

        # Отправляем в n8n
        response = await call_bot_instructor_n8n(payload)

        # Получаем ответ
        answer = response.get("answer", "Извините, не смог обработать ваш запрос.")

        await message.answer(
            f"🧠 <b>Ответ инструктора:</b>\n\n{answer}\n\n"
            f"Задайте следующий вопрос или вернитесь в меню:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📚 Выбрать другую тему")],
                    [KeyboardButton(text="✅ Завершить инструктаж")],
                ],
                resize_keyboard=True,
            ),
        )

        await state.set_state(BotInstructorState.IN_CONVERSATION)

    except Exception as e:
        logger.error(f"Error processing instructor query: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке запроса. Попробуйте еще раз.",
            reply_markup=_safety_menu_keyboard(),
        )
        await state.clear()


@router.message(BotInstructorState.IN_CONVERSATION, F.text == "📚 Выбрать другую тему")
async def back_to_topics(message: types.Message, state: FSMContext):
    """Возвращает к выбору темы инструктажа."""

    await state.set_state(BotInstructorState.WAITING_FOR_TOPIC)

    await message.answer(
        "Выберите новую тему:",
        reply_markup=_instructor_topics_keyboard(),
    )


@router.message(BotInstructorState.IN_CONVERSATION, F.text == "✅ Завершить инструктаж")
async def end_instructor_session(message: types.Message, state: FSMContext):
    """Завершает сессию с ботом-инструктором."""

    data = await state.get_data()

    try:
        # Уведомляем n8n о завершении сессии
        payload = {
            "telegram_id": message.from_user.id,
            "action": "end_session",
        }
        await call_bot_instructor_n8n(payload)
    except Exception as e:
        logger.error(f"Error ending instructor session: {e}")

    await state.clear()

    await message.answer(
        "✅ <b>Инструктаж завершен</b>\n\n"
        "Спасибо за внимание к вопросам охраны труда!\n"
        "Помните: ваша безопасность - наш приоритет.",
        parse_mode="HTML",
        reply_markup=_safety_menu_keyboard(),
    )


@router.message(BotInstructorState.IN_CONVERSATION)
async def continue_instructor_conversation(message: types.Message, state: FSMContext):
    """Продолжает диалог с ботом-инструктором."""

    await process_instructor_query(message, state, message.text)


def register_handlers(parent_router: Router):
    """Регистрирует обработчики бота-инструктора."""
    parent_router.include_router(router)

