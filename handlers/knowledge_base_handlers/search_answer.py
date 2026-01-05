"""Обработчик раздела 'Найти ответ' (Корпоративная база знаний)."""

import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import httpx

logger = logging.getLogger(__name__)
router = Router()

# ⚠️ Вставь сюда URL твоего НОВОГО вебхука из n8n (Company RAG)
N8N_COMPANY_WEBHOOK_URL = "https://levinbiz.app.n8n.cloud/webhook/company-rag"

class CompanyKBState(StatesGroup):
    waiting_for_question = State()

# --- Кнопки-подсказки (Самое важное для Демо) ---
def _company_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌴 Оформление отпуска"), KeyboardButton(text="💰 Дни выплаты зарплаты")],
            [KeyboardButton(text="🤒 Больничный лист"), KeyboardButton(text="🏥 ДМС и страховка")],
            [KeyboardButton(text="🏠 Удаленная работа"), KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Спросите о жизни компании..."
    )

def _main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Вернуться в главное меню (твое основное меню)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔎 Найти ответ")],
            [KeyboardButton(text="🚀 Курс молодого бойца")],
            [KeyboardButton(text="📂 Библиотека")],
            # ... добавь сюда свои кнопки выхода если есть
        ],
        resize_keyboard=True
    )

# --- Логика запроса ---
async def ask_company_rag(question: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Отправляем в n8n просто query
            response = await client.post(
                N8N_COMPANY_WEBHOOK_URL,
                json={"query": question}
            )
            response.raise_for_status()
            # Ждем ответ в поле 'answer' (как настраивали раньше)
            return response.json().get("answer", "⚠️ Ошибка AI.")
    except Exception as e:
        logger.error(f"Company RAG Error: {e}")
        return "😔 База знаний сейчас отдыхает. Попробуйте позже."

# --- Хендлеры ---

@router.message(F.text == "🔎 Найти ответ")
async def start_company_kb(message: types.Message, state: FSMContext):
    await state.set_state(CompanyKBState.waiting_for_question)

    await message.answer(
        "📂 <b>Корпоративная База Знаний (AI)</b>\n\n"
        "Больше не нужно ждать ответа от HR или искать нужный файл в папках.\n"
        "Я проанализировала все внутренние регламенты, приказы и инструкции.\n\n"
        "⏱ <b>Я экономлю Ваше время.</b> Спросите меня про:\n"
        "• 💰 Даты выплат и систему бонусов\n"
        "• 🌴 Оформление отпусков и отгулов\n"
        "• 🏥 ДМС, больничные и справки\n\n"
        "👇 <b>Нажмите на тему или задайте вопрос своими словами:</b>",
        parse_mode="HTML",
        reply_markup=_company_menu_keyboard()
    )

@router.message(CompanyKBState.waiting_for_question, F.text == "🔙 Назад")
async def exit_kb(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выход в главное меню.", reply_markup=_main_menu_keyboard())

@router.message(CompanyKBState.waiting_for_question)
async def process_question(message: types.Message):
    # Показываем статус "печатает..."
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    answer = await ask_company_rag(message.text)

    await message.answer(
        f"🤖 <b>Ответ HR-ассистента:</b>\n\n{answer}",
        parse_mode="HTML",
        reply_markup=_company_menu_keyboard() # Оставляем кнопки, чтобы можно было спросить еще что-то
    )

def register_handlers(parent_router: Router):
    parent_router.include_router(router)