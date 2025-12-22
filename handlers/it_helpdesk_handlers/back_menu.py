"""Обработчик кнопки Назад из IT HelpDesk в главное меню."""

from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from states import BotStates

router = Router()


def _main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🤝 HR и найм"), KeyboardButton(text="👷‍♂️ Охрана труда")],
            [KeyboardButton(text="🛠 IT HelpDesk"), KeyboardButton(text="🧠 База Знаний")],
            [KeyboardButton(text="💰 AI-Менеджер")],
        ],
        resize_keyboard=True,
    )


@router.message(F.text == "🔙 Назад")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    # Устанавливаем состояние главного меню
    await state.set_state(BotStates.MAIN_MENU)

    await message.answer(
        "Возвращаю в главное меню. Выберите отдел:",
        reply_markup=_main_menu_keyboard(),
    )


def register_handlers(parent_router: Router):
    parent_router.include_router(router)

