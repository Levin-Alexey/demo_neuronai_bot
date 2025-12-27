"""Обработчик кнопки Охрана труда"""

import os
from aiogram import types, F, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext

from states import BotStates
from handlers.safety_handlers import menu

router = Router()


def _labor_safety_keyboard() -> ReplyKeyboardMarkup:
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


@router.message(F.text == "👷‍♂️ Охрана труда")
async def labor_safety_handler(message: types.Message, state: FSMContext):
    """Отображает меню Охраны труда с основными функциями."""
    print(f"✅ LABOR SAFETY HANDLER TRIGGERED! Text: {message.text!r}")

    # Если пользователь был в другом разделе, очищаем состояние
    current_state = await state.get_state()
    if current_state and current_state != BotStates.LABOR_SAFETY_MENU:
        await state.clear()

    # Устанавливаем состояние меню охраны труда
    await state.set_state(BotStates.LABOR_SAFETY_MENU)

    video_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "safe.mp4")
    try:
        if os.path.exists(video_path):
            video = FSInputFile(video_path)
            await message.answer_video_note(video)
    except Exception as e:
        print(f"Error sending safety video note: {e}")

    menu_text = (
        "👷‍♂️ <b>Модуль \"Безопасность труда\" активирован</b>\n"
        "Системы мониторинга запущены. Я готова обеспечить безопасность на объекте и производстве 24/7. Забудьте про бумажные журналы и долгие инструктажи.\n\n"
        "<b>Ваши инструменты защиты:</b>\n"
        "📸 <b>Фото-контроль (AI Vision):</b> Нейросеть проверит наличие каски, жилета и страховочной привязи по одному фото. <i>(Авто-генерация пропуска на смену).</i>\n"
        "📝 <b>Цифровой Наряд-допуск:</b> Заполнение чек-листа опасных работ прямо в чате.\n"
        "🆘 <b>Тревожная кнопка:</b> Мгновенное оповещение службы безопасности о рисках (обрыв кабеля, разлив химии, отсутствие ограждения).\n"
        "🧠 <b>Бот-Инструктор:</b> RAG-система, знающая все ГОСТы, СНиПы и ваши внутренние регламенты.\n\n"
        "👇 <b>Выберите действие:</b>"
    )

    await message.answer(
        menu_text,
        parse_mode="HTML",
        reply_markup=_labor_safety_keyboard(),
    )


def register_handlers(dp):
    """Регистрация обработчиков Охраны труда"""
    dp.include_router(router)
    # Регистрируем подменю
    menu.register_handlers(dp)
