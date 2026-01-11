"""
Обработчик раздела '💰 Расчет стоимости'.
Production-версия: Сбор данных -> RAG (Прайс) -> КП -> Email админу.
"""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import httpx
import logging
from aiogram.filters import Command

from states import BotStates

logger = logging.getLogger(__name__)
router = Router()

# ⚠️ Вставь URL нового вебхука "Sales Calculator"
N8N_SALES_WEBHOOK_URL = "https://levinbiz.app.n8n.cloud/webhook/sales-calc"

# ID менеджера (ваш Telegram ID)
MANAGER_CHAT_ID = 525944420  # Замените на ваш реальный ID
MANAGER_USERNAME = "LevinMSK"  # Ваш username

class SalesState(StatesGroup):
    waiting_for_niche = State()
    waiting_for_task = State()
    waiting_for_budget = State()
    waiting_for_contact = State()

class ManagerState(StatesGroup):
    waiting_for_message = State()

def _cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True
    )

# --- ГЛАВНОЕ МЕНЮ AI-МЕНЕДЖЕРА ---
@router.message(F.text == "💰 AI-Менеджер")
async def ai_manager_main_menu(message: types.Message, state: FSMContext):
    """Обработчик кнопки AI-Менеджер из главного меню"""
    await state.set_state(BotStates.AI_MANAGER_MENU)

    manager_text = """💰 <b>AI-Менеджер</b>

Добро пожаловать в отдел продаж будущего.

Мой AI рассчитает смету вашего проекта на основе актуальных прайс-листов.

Что хотите сделать?"""

    manager_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Расчет стоимости")],
            [KeyboardButton(text="🔙 Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(manager_text, parse_mode="HTML", reply_markup=manager_keyboard)

# --- 1. Старт опроса ---
@router.message(F.text == "💰 Расчет стоимости")
async def start_sales(message: types.Message, state: FSMContext):
    await state.set_state(SalesState.waiting_for_niche)
    await message.answer(
        "💼 <b>AI-Калькулятор стоимости</b>\n\n"
        "Я обучен на актуальных прайс-листах нашей студии.\n"
        "Ответьте на 4 вопроса, и я сформирую персональное предложение, а также уведомлю руководителя.\n\n"
        "1️⃣ <b>Какая у вас сфера бизнеса?</b>",
        parse_mode="HTML",
        reply_markup=_cancel_kb()
    )

# --- 2. Ниша -> Задача ---
@router.message(SalesState.waiting_for_niche, F.text != "❌ Отмена")
async def step_niche(message: types.Message, state: FSMContext):
    await state.update_data(niche=message.text)
    await state.set_state(SalesState.waiting_for_task)
    await message.answer(
        "2️⃣ <b>Опишите задачу своими словами.</b>\n"
        "Например: <i>'Хочу бота, который отвечает на вопросы по PDF и записывает на прием'</i>",
        parse_mode="HTML",
        reply_markup=_cancel_kb()
    )

# --- 3. Задача -> Бюджет ---
@router.message(SalesState.waiting_for_task, F.text != "❌ Отмена")
async def step_task(message: types.Message, state: FSMContext):
    await state.update_data(task=message.text)
    await state.set_state(SalesState.waiting_for_budget)

    # Кнопки для удобства
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="до 50 000 руб"), KeyboardButton(text="50-150 тыс. руб")],
            [KeyboardButton(text="150-300 тыс. руб"), KeyboardButton(text="Бюджет не ограничен")],
            [KeyboardButton(text="❌ Отмена")]
        ], resize_keyboard=True
    )
    await message.answer("3️⃣ <b>На какой бюджет вы ориентируетесь?</b>", reply_markup=kb)

# --- 4. Бюджет -> Контакт ---
@router.message(SalesState.waiting_for_budget, F.text != "❌ Отмена")
async def step_budget(message: types.Message, state: FSMContext):
    await state.update_data(budget=message.text)
    await state.set_state(SalesState.waiting_for_contact)

    await message.answer(
        "4️⃣ <b>Как с вами связаться?</b>\n"
        "Напишите телефон или @username (или нажмите кнопку ниже).",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Отправить мой контакт", request_contact=True)],
                [KeyboardButton(text="❌ Отмена")]
            ], resize_keyboard=True
        )
    )

# --- 5. Финал: Отправка в n8n ---
@router.message(SalesState.waiting_for_contact) # Ловим текст
async def finish_sales_text(message: types.Message, state: FSMContext):
    contact = message.text
    await process_sales_final(message, state, contact)

@router.message(F.contact) # Ловим кнопку контакта
async def finish_sales_contact(message: types.Message, state: FSMContext):
    contact = f"{message.contact.phone_number} ({message.contact.first_name})"
    await process_sales_final(message, state, contact)

async def process_sales_final(message: types.Message, state: FSMContext, contact: str):
    data = await state.get_data()

    # Анимация "печатает" (пока n8n думает)
    msg = await message.answer("⏳ <b>AI анализирует задачу и считает смету...</b>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Готовим данные для n8n
        payload = {
            "niche": data['niche'],
            "task": data['task'],
            "budget": data['budget'],
            "contact": contact,
            "username": message.from_user.username
        }

        # Отправляем в n8n
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(N8N_SALES_WEBHOOK_URL, json=payload)

            if response.status_code == 200:
                answer = response.json().get("answer", "Ошибка генерации КП.")

                # Удаляем сообщение "анализирую" и шлем результат
                await msg.delete()
                await message.answer(
                    f"📝 <b>Ваше предварительное КП:</b>\n\n{answer}\n\n"
                    f"✅ <i>Ваш запрос и контакты уже переданы руководителю проекта.</i>",
                    parse_mode="Markdown" # GPT любит markdown (**bold**)
                )
            else:
                await msg.edit_text("❌ Ошибка связи с сервером расчета.")

    except Exception as e:
        logger.error(f"Sales Error: {e}")
        await msg.edit_text("😔 Произошла ошибка. Мы уже чиним.")

    await state.clear()
    # Тут можно вернуть главное меню

# Отмена
@router.message(F.text == "❌ Отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Расчет отменен.", reply_markup=types.ReplyKeyboardRemove())

@router.message(F.text == "🔙 Назад в меню")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()

    from main import cmd_start
    await cmd_start(message, state)

# --- МЕНЕДЖЕР РАЗДЕЛ ---

@router.message(Command("manager"))
async def manager_command(message: types.Message, state: FSMContext):
    """Обработчик команды /manager"""
    await start_manager_contact(message, state)

@router.message(F.text == "👤 Связаться с менеджером")
async def manager_button_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки 'Связаться с менеджером'"""
    await start_manager_contact(message, state)

async def start_manager_contact(message: types.Message, state: FSMContext):
    """Начало процесса связи с менеджером"""
    await state.set_state(ManagerState.waiting_for_message)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

    await message.answer(
        "📞 <b>Связь с менеджером</b>\n\n"
        "Напишите ваше сообщение. Вы можете отправить текст, файл или фото.\n"
        "Менеджер ответит вам в ближайшее время.",
        parse_mode="HTML",
        reply_markup=kb
    )

@router.message(ManagerState.waiting_for_message, F.text == "❌ Отмена")
async def cancel_manager(message: types.Message, state: FSMContext):
    """Отмена связи с менеджером"""
    await state.clear()
    await message.answer("Отменено.", reply_markup=types.ReplyKeyboardRemove())

@router.message(ManagerState.waiting_for_message, F.text)
async def manager_text_message(message: types.Message, state: FSMContext):
    """Обработка текстового сообщения для менеджера"""
    user_info = f"<b>Сообщение от пользователя:</b>\n" \
                f"<b>ID:</b> {message.from_user.id}\n" \
                f"<b>Имя:</b> {message.from_user.first_name} {message.from_user.last_name or ''}\n" \
                f"<b>Username:</b> @{message.from_user.username or 'не указан'}\n" \
                f"<b>Сообщение:</b>\n{message.text}"

    try:
        await message.bot.send_message(
            chat_id=525944420,  # Ваш ID (замените)
            text=user_info,
            parse_mode="HTML"
        )
        await message.answer(
            "✅ Ваше сообщение отправлено менеджеру!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Manager message error: {e}")
        await message.answer(
            "❌ Ошибка при отправке сообщения. Попробуйте позже.",
            reply_markup=types.ReplyKeyboardRemove()
        )

    await state.clear()

@router.message(ManagerState.waiting_for_message, F.document)
async def manager_document_message(message: types.Message, state: FSMContext):
    """Обработка файла для менеджера"""
    user_info = f"<b>Файл от пользователя:</b>\n" \
                f"<b>ID:</b> {message.from_user.id}\n" \
                f"<b>Имя:</b> {message.from_user.first_name} {message.from_user.last_name or ''}\n" \
                f"<b>Username:</b> @{message.from_user.username or 'не указан'}\n" \
                f"<b>Файл:</b> {message.document.file_name}"

    try:
        await message.bot.send_message(
            chat_id=525944420,  # Ваш ID (замените)
            text=user_info,
            parse_mode="HTML"
        )
        await message.bot.send_document(
            chat_id=525944420,  # Ваш ID (замените)
            document=message.document.file_id
        )
        await message.answer(
            "✅ Ваш файл отправлен менеджеру!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Manager document error: {e}")
        await message.answer(
            "❌ Ошибка при отправке файла. Попробуйте позже.",
            reply_markup=types.ReplyKeyboardRemove()
        )

    await state.clear()

@router.message(ManagerState.waiting_for_message, F.photo)
async def manager_photo_message(message: types.Message, state: FSMContext):
    """Обработка фото для менеджера"""
    user_info = f"<b>Фото от пользователя:</b>\n" \
                f"<b>ID:</b> {message.from_user.id}\n" \
                f"<b>Имя:</b> {message.from_user.first_name} {message.from_user.last_name or ''}\n" \
                f"<b>Username:</b> @{message.from_user.username or 'не указан'}"

    try:
        await message.bot.send_message(
            chat_id=525944420,  # Ваш ID (замените)
            text=user_info,
            parse_mode="HTML"
        )
        await message.bot.send_photo(
            chat_id=525944420,  # Ваш ID (замените)
            photo=message.photo[-1].file_id
        )
        await message.answer(
            "✅ Ваше фото отправлено менеджеру!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Manager photo error: {e}")
        await message.answer(
            "❌ Ошибка при отправке фото. Попробуйте позже.",
            reply_markup=types.ReplyKeyboardRemove()
        )

    await state.clear()

def register_handlers(parent_router: Router):
    parent_router.include_router(router)