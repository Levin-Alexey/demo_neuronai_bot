"""Обработчик кнопки 'Назад в меню' для раздела База Знаний"""

from aiogram import types, F, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from states import BotStates

router = Router()


@router.message(F.text == "🔙 Назад в меню")
async def back_menu_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки 'Назад в меню' из раздела База Знаний"""
    # Проверяем текущее состояние - если мы в меню Базы Знаний, то возвращаем главное меню
    current_state = await state.get_state()

    if current_state == BotStates.KNOWLEDGE_BASE_MENU or "knowledge_base" in str(current_state):
        # Возвращаем в главное меню
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="🤝 HR и найм"),
                    KeyboardButton(text="👷‍♂️ Охрана труда"),
                ],
                [
                    KeyboardButton(text="🛠 IT HelpDesk"),
                    KeyboardButton(text="🧠 База Знаний"),
                ],
                [
                    KeyboardButton(text="💰 AI-Менеджер"),
                ]
            ],
            resize_keyboard=True
        )

        await message.answer("Вы вернулись в главное меню", reply_markup=keyboard)
        await state.set_state(BotStates.MAIN_MENU)


def register_handlers(router_obj):
    """Регистрация обработчиков меню"""
    router_obj.include_router(router)

