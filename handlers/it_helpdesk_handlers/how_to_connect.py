"""Демонстрация RAG на IT-документации"""

import asyncio
import logging
import httpx
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Импортируем клавиатуру возврата в меню IT HelpDesk
from handlers.it_helpdesk_handlers.smart_ticket import get_helpdesk_keyboard

router = Router()
logger = logging.getLogger(__name__)

# Тот же вебхук, просто поменяем промпт внутри n8n
N8N_RAG_WEBHOOK = "https://levinbiz.app.n8n.cloud/webhook/rag-demo"

# Состояния
class RAGDemoState(StatesGroup):
    waiting_for_question = State()

def get_exit_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Завершить тест")]],
        resize_keyboard=True
    )

@router.message(F.text == "❓ Как подключить")
async def start_it_rag_demo(message: types.Message, state: FSMContext):
    """Демонстрация RAG на IT-документации."""
    
    # 1. Продающий текст (Акцент на IT-инфраструктуре)
    info_text = (
        "🧠 <b>Технология RAG: Подключение к IT-Базе Знаний</b>\n\n"
        "Ваши сотрудники задают одни и те же вопросы: «Как настроить VPN?», «Где скачать антивирус?», «Как сбросить пароль?». "
        "Инженеры тратят часы, копируя ссылки на Wiki.\n\n"
        "<b>Я решаю это иначе.</b> Я подключаюсь к Вашей Confluence/Jira, индексирую техническую документацию и отвечаю пользователям мгновенно.\n\n"
        "⚙️ <i>Инициализация IT-контура...</i>"
    )
    msg = await message.answer(info_text, parse_mode="HTML")
    
    # Анимация загрузки "тяжелых" данных
    await asyncio.sleep(1.0)
    await msg.edit_text(info_text + "\n📥 <i>Импорт протоколов безопасности (ISO 27001)...</i>", parse_mode="HTML")
    await asyncio.sleep(1.0)
    await msg.edit_text(info_text + "\n🔗 <i>Индексация сетевых настроек и доступов...</i>", parse_mode="HTML")
    await asyncio.sleep(0.8)
    await msg.edit_text(info_text + "\n✅ <b>IT-База Знаний подключена.</b>", parse_mode="HTML")
    
    await asyncio.sleep(0.5)
    
    # 2. Призыв к тесту (Строго по IT)
    await state.set_state(RAGDemoState.waiting_for_question)
    
    await message.answer(
        "💻 <b>Демо-режим: «Новый сотрудник»</b>\n\n"
        "Представьте, что Вы пришли в компанию и Вам нужно настроить рабочее место. "
        "Я загрузил в память <b>внутренние IT-регламенты</b>.\n\n"
        "<b>Темы, которые я теперь знаю:</b>\n"
        "🔐 Настройка VPN и удаленного доступа\n"
        "📶 Пароли от офисного Wi-Fi (Гостевой/Служебный)\n"
        "🎫 Правила создания тикетов в Jira\n"
        "🛡 Политика смены паролей\n\n"
        "👇 <b>Спросите меня о чем-то техническом.</b>\n"
        "<i>(Например: «Какой пароль от вайфая для гостей?» или «Как подключиться к VPN из дома?»)</i>",
        parse_mode="HTML",
        reply_markup=get_exit_keyboard()
    )

@router.message(RAGDemoState.waiting_for_question, F.text != "🔙 Завершить тест")
async def process_it_rag_question(message: types.Message):
    """Отправка вопроса в n8n."""
    
    user_question = message.text
    status_msg = await message.answer("terminal@bot:~$ <i>grep 'search_query' /var/docs/wiki...</i>", parse_mode="HTML")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                N8N_RAG_WEBHOOK, 
                json={"question": user_question}
            )
            
            logger.info(f"n8n response status: {resp.status_code}")
            logger.info(f"n8n response body: {resp.text}")
            
            # Проверяем статус ответа
            if resp.status_code != 200:
                await status_msg.edit_text(
                    f"❌ Ошибка сервера: HTTP {resp.status_code}\n"
                    f"Webhook может быть неактивен или неправильно настроен."
                )
                return
            
            # Пробуем распарсить JSON
            try:
                result = resp.json()
                logger.info(f"Parsed JSON: {result}")
            except Exception as json_err:
                await status_msg.edit_text(
                    f"❌ Ошибка парсинга ответа: {json_err}\n"
                    f"Ответ сервера: {resp.text[:200]}"
                )
                return
            
            # Извлекаем ответ (пробуем разные варианты ключей)
            answer_text = result.get('answer') or result.get('response') or result.get('output')
            
            if not answer_text:
                # Если нет нужных ключей, показываем весь ответ
                await status_msg.edit_text(
                    f"⚠️ Получен ответ от сервера, но не найдено поле 'answer'.\n\n"
                    f"Полный ответ:\n```json\n{result}\n```",
                    parse_mode="Markdown"
                )
                return
            
            await status_msg.edit_text(answer_text, parse_mode="Markdown")
            
    except httpx.TimeoutException:
        await status_msg.edit_text("❌ Timeout: Сервер n8n не отвечает более 30 секунд.")
    except httpx.ConnectError:
        await status_msg.edit_text(
            "❌ Connection Error: Не удалось подключиться к серверу n8n.\n"
            "Проверьте URL вебхука и доступность сервера."
        )
    except Exception as e:
        logger.exception("Error in RAG question processing")
        await status_msg.edit_text(f"❌ System Error: {type(e).__name__}: {e}")

@router.message(RAGDemoState.waiting_for_question, F.text == "🔙 Завершить тест")
async def exit_rag_demo(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Сессия завершена.\n\n"
        "Точно так же я могу выучить Вашу документацию по <b>1С, API, серверам или Cybersecurity</b>.",
        parse_mode="HTML",
        reply_markup=get_helpdesk_keyboard()
    )


def register_handlers(parent_router: Router):
    parent_router.include_router(router)

