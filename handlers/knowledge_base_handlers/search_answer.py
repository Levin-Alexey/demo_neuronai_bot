"""Обработчик подраздела 'Найти ответ'"""

from aiogram import types, F, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from states import BotStates

router = Router()


@router.message(F.text == "🔎 Найти ответ")
async def search_answer_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки 'Найти ответ'"""
    search_text = """🔎 Найти ответ

В этом разделе вы можете быстро найти ответ на интересующий вас вопрос.

Система поиска может ответить на вопросы:
    • По основным процессам компании
    • По кадровым вопросам
    • По регламентам и правилам
    • По социальным гарантиям

Напишите ваш вопрос, и ИИ найдет ответ в базе знаний:"""

    # Создаем клавиатуру для возврата
    kb_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(search_text, parse_mode="HTML", reply_markup=kb_keyboard)
    await state.set_state(BotStates.KNOWLEDGE_BASE_MENU)


def register_handlers(router_obj):
    """Регистрация обработчиков поиска"""
    router_obj.include_router(router)

