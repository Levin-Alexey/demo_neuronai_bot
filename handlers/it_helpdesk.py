"""Обработчик кнопки IT HelpDesk"""

import os
from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext

from states import BotStates
from handlers.it_helpdesk_handlers import menu

router = Router()


def _it_helpdesk_keyboard() -> ReplyKeyboardMarkup:
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


@router.message(F.text == "🛠 IT HelpDesk")
async def it_helpdesk_menu(message: types.Message, state: FSMContext):
    """Отображает меню IT HelpDesk с основными действиями."""
    print(f"✅ IT HELPDESK HANDLER TRIGGERED! Text: {message.text!r}")

    # Если пользователь был в собеседовании, отменяем его
    current_state = await state.get_state()
    if current_state == BotStates.INTERVIEW:
        try:
            from handlers.hr_handlers.interview import end_session, call_n8n
            telegram_id = message.from_user.id
            # Уведомляем n8n о завершении
            await call_n8n({
                "action": "cancel",
                "telegram_id": telegram_id,
            })
            # Завершаем сессию
            end_session(telegram_id)
        except Exception as e:
            print(f"Error ending interview session: {e}")
    # Отправляем видео в кружочке (Video Note)
    video_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "1221.mp4")
    try:
        if os.path.exists(video_path):
            video = FSInputFile(video_path)
            await message.answer_video_note(video)
    except Exception as e:
        print(f"Error sending video: {e}")
    
    menu_text = (
        "🦾 <b>Системы в норме. Я готова к работе.</b>\n\n"
        "Вы только что увидели будущее техподдержки. Забудьте о тикетах, которые висят сутками. Моя задача - устранять неисправности раньше, чем они остановят Ваш бизнес.\n\n"
        "Передо мной Ваш <b>пульт управления стабильностью</b>. Выберите инструмент:\n\n"
        "🔍 <b>AI-Глаз</b> - Пришли фото ошибки. Я «прочитаю» его и найду решение.\n"
        "⚡️ <b>Мгновенное действие</b> - Для типовых задач за 5 секунд (сброс пароля, доступ, ребут).\n"
        "📋 <b>Умный Тикет</b> - Если проблема сложная и требует глубокого анализа.\n"
        "❓ <b>Как подключить</b> - Ваша база знаний, которая доступна 24/7.\n\n"
        "👇 <i>Выбирайте пунк меню!</i>"
    )
    await message.answer(menu_text, parse_mode="HTML", reply_markup=_it_helpdesk_keyboard())

    # Устанавливаем состояние IT HelpDesk
    await state.set_state(BotStates.IT_HELPDESK_MENU)


def register_handlers(dp):
    """Регистрация обработчиков IT HelpDesk."""
    dp.include_router(router)
    # Регистрируем подменю IT HelpDesk
    menu.register_handlers(router)
