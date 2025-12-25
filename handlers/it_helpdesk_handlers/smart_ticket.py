"""Модуль Smart Ticket: создание структурированных тикетов с помощью n8n/AI."""

import asyncio
import logging
import httpx
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

router = Router()
logger = logging.getLogger(__name__)


# --- Состояния FSM для Smart Ticket ---
class SmartTicketState(StatesGroup):
    waiting_for_ticket_description = State()


# --- Клавиатура IT HelpDesk (возврат в раздел и назад) ---
def get_helpdesk_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 AI-Глаз")],
            [KeyboardButton(text="⚡ Мгновенное действие")],
            [KeyboardButton(text="📋 Умный Тикет")],
            [KeyboardButton(text="❓ Как подключить")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )


# URL вебхука n8n (замените на свой при деплой)
N8N_TICKET_WEBHOOK = "https://levinbiz.app.n8n.cloud/webhook/smart-ticket"


# --- Функция запроса в n8n ---
async def analyze_ticket_with_n8n(user_text: str, user_name: str) -> dict:
    """Отправляем текст в n8n, чтобы ИИ превратил его в тикет."""

    payload = {
        "text": user_text,
        "user": user_name,
    }

    # Таймаут 30 сек, так как n8n может думать
    # n8n Cloud: иногда требуется verify=False и тестовый режим вебхука
    async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True) as client:
        try:
            resp = await client.post(N8N_TICKET_WEBHOOK, json=payload)
            status = resp.status_code
            text = resp.text
            logger.info(f"[SmartTicket->n8n] status={status} body={text[:200]}")

            # n8n test webhook (404 с подсказкой) — вернуть понятный ответ
            if status == 404 and "requested webhook" in text:
                return {
                    "ticket_id": "TEST-MODE",
                    "title": "Вебхук не активирован (test mode)",
                    "category": "System",
                    "priority": "Low",
                    "summary": (
                        "В n8n нужно нажать 'Execute workflow' перед тестовым вызовом "
                        "вебхука или опубликовать продовый вебхук /webhook/..."
                    ),
                    "solution_hint": "Откройте workflow в n8n и нажмите Execute.",
                }

            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Ошибка запроса в n8n: {type(e).__name__}: {e}")
            # Возвращаем заглушку, чтобы демо не сломалось при ошибке сети
            return {
                "ticket_id": "ERR-DEMO",
                "title": "Ошибка соединения с AI",
                "category": "System",
                "priority": "Low",
                "summary": user_text,  # Возвращаем исходный текст
                "solution_hint": "Пожалуйста, попробуйте позже.",
            }


# --- Точка входа: активация Smart Ticket ---
@router.message(F.text == "📋 Умный Тикет")
async def smart_ticket_handler(message: types.Message, state: FSMContext):
    # Ждем текстовое описание инцидента от пользователя
    await state.set_state(SmartTicketState.waiting_for_ticket_description)

    await message.answer(
        "📋 <b>Модуль \"Smart Ticket\" активирован</b>\n\n"
        "Сложные проблемы требуют порядка. Но заполнять бесконечные формы в "
        "Jira "
        "или Service Desk - это боль.\n"
        "Я беру эту рутину на себя. Я выступлю в роли первой линии поддержки "
        "(L1).\n\n"
        "🤖 <b>Как это работает:</b>\n"
        "1. <b>Диалог:</b> Вы описываете проблему своими словами в чат.\n"
        "2. <b>Интервью:</b> Если деталей мало, я задам 1-2 уточняющих "
        "вопроса "
        "(как живой админ).\n"
        "3. <b>Оформление:</b> Я сам определю приоритет (SLA), категорию и "
        "отправлю структурированную задачу в Task-трекер.\n\n"
        "🎯 <b>Итог:</b> Разработчики получат идеальный тикет, а вы - номер "
        "заявки "
        "за 30 секунд.\n\n"
        "👇 <b>Опишите, что случилось?</b>\n"
        "<i>(Например: \"У нового сотрудника нет доступа к сетевой папке "
        "Маркетинга\")</i>",
        parse_mode="HTML",
    )


# --- Обработчик текста (создание тикета) ---
@router.message(SmartTicketState.waiting_for_ticket_description, F.text)
async def process_ticket_real_ai(message: types.Message, state: FSMContext):
    user_text = message.text or ""
    user_name = message.from_user.full_name if message.from_user else ""

    # 1) Эффект "Работающего ИИ" (Immersive Loading)
    status_msg = await message.answer(
        "🧠 <i>Нейросеть читает ваш запрос...</i>",
        parse_mode="HTML",
    )

    # Запускаем запрос в n8n параллельно с анимацией статусов
    n8n_task = asyncio.create_task(
        analyze_ticket_with_n8n(user_text, user_name)
    )

    await asyncio.sleep(1.0)
    await status_msg.edit_text(
        "🔍 <i>Классификация инцидента и поиск в базе знаний...</i>",
        parse_mode="HTML",
    )
    await asyncio.sleep(1.0)
    await status_msg.edit_text(
        "⚖️ <i>Оценка SLA и приоритета (Matrix Impact)...</i>",
        parse_mode="HTML",
    )
    await asyncio.sleep(0.8)
    await status_msg.edit_text(
        "📝 <i>Формирование карточки тикета в Jira...</i>", parse_mode="HTML"
    )

    # Ждем ответ от n8n
    ai_data = await n8n_task

    # 2) Карточка тикета
    tid = ai_data.get("ticket_id", "REQ-000")
    result_text = (
        f"🎫 <b>Тикет #{tid} зарегистрирован</b>\n"
        f"──────────────────────\n"
        f"📂 <b>Категория:</b> {ai_data.get('category')}\n"
        f"⚡ <b>Приоритет:</b> {ai_data.get('priority')}\n"
        f"📌 <b>Тема:</b> {ai_data.get('title')}\n\n"
        f"📝 <b>Профессиональное описание (AI):</b>\n"
        f"<i>«{ai_data.get('summary')}»</i>\n\n"
        f"💡 <b>Рекомендация админу:</b>\n"
        f"{ai_data.get('solution_hint')}"
    )

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(
            text="🔗 Открыть в Tracker (Demo)", url="https://jira.atlassian.com"
        )]]
    )

    # Удаляем сообщение с загрузкой и отправляем результат
    try:
        await status_msg.delete()
    except Exception:
        pass

    await message.answer(
        result_text,
        parse_mode="HTML",
        reply_markup=inline_kb,
    )

    # Возврат клавиатуры меню IT HelpDesk
    await message.answer(
        "Тикет создан. Что делаем дальше?",
        reply_markup=get_helpdesk_keyboard(),
    )

    # Сбрасываем состояние
    await state.clear()


def register_handlers(parent_router: Router):
    parent_router.include_router(router)

