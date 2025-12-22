"""Обработчик раздела "Мгновенное действие" с FSM и симуляцией шагов."""

import asyncio
import random
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


router = Router()


# --- Состояния FSM ---
class InstantActionState(StatesGroup):
    waiting_for_selection = State()


# --- Клавиатуры ---
def get_instant_actions_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора быстрых действий."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔑 Сбросить пароль")],
            [KeyboardButton(text="🔓 Разблокировать (Unlock)")],
            [KeyboardButton(text="🌐 Рестарт VPN-сессии")],
            [KeyboardButton(text="🔙 Назад в меню")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите скрипт автоматизации...",
    )


def get_helpdesk_main_keyboard() -> ReplyKeyboardMarkup:
    """Возврат в главное меню HelpDesk (упрощенная для примера)."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛠 IT HelpDesk")],
        ],
        resize_keyboard=True,
    )


# --- 1. Главный экран раздела "Мгновенное действие" ---
@router.message(F.text == "⚡ Мгновенное действие")
async def start_instant_actions_mode(message: types.Message, state: FSMContext):
    """Вход в режим мгновенных действий с расширенным текстом."""

    await state.set_state(InstantActionState.waiting_for_selection)

    await message.answer(
        "⚡ <b>Протокол \"Instant Fix\" инициирован</b>\n\n"
        "Ждать системного администратора 20 минут ради сброса пароля - это непозволительная роскошь.\n"
        "Я подключен напрямую к корпоративному <b>Active Directory</b> и шлюзам безопасности.\n\n"
        "⏱ <b>Мое время реакции:</b> 1.2 секунды.\n"
        "🔒 <b>Безопасность:</b> Двухфакторная верификация (2FA).\n\n"
        "👇 <b>Какую операцию выполнить прямо сейчас?</b>",
        parse_mode="HTML",
        reply_markup=get_instant_actions_keyboard(),
    )


# --- 2. Обработчики кнопок (Симуляция работы) ---
@router.message(InstantActionState.waiting_for_selection, F.text == "🔑 Сбросить пароль")
async def simulate_password_reset(message: types.Message):
    """Симуляция сброса пароля с визуальными шагами."""

    status_msg = await message.answer("🔄 <i>Устанавливаю защищенное соединение с LDAP...</i>", parse_mode="HTML")
    await asyncio.sleep(1.0)

    steps = [
        "👤 <i>Поиск учетной записи пользователя...</i>",
        "🔐 <i>Проверка токена безопасности (Security Token)...</i>",
        "⚙️ <i>Генерация временного пароля (Strong Policy)...</i>",
        "📡 <i>Синхронизация с облаком...</i>",
    ]

    for step in steps:
        await asyncio.sleep(0.8)
        try:
            await status_msg.edit_text(step, parse_mode="HTML")
        except Exception:
            pass

    temp_password = f"Neuron{random.randint(100, 999)}!Fix"

    final_text = (
        "✅ <b>Пароль успешно сброшен!</b>\n\n"
        f"Ваш временный пароль: <code>{temp_password}</code>\n\n"
        "⚠️ <i>Система потребует сменить его при первом входе.</i>\n"
        "<i>Действие залогировано в Security Audit Log.</i>"
    )

    await status_msg.delete()
    await message.answer(final_text, parse_mode="HTML", reply_markup=get_instant_actions_keyboard())


@router.message(InstantActionState.waiting_for_selection, F.text.contains("Разблокировать"))
async def simulate_account_unlock(message: types.Message):
    """Симуляция разблокировки учетной записи."""

    status_msg = await message.answer("🔄 <i>Проверка статуса учетной записи в AD...</i>", parse_mode="HTML")
    await asyncio.sleep(1.5)

    await status_msg.edit_text("🔓 <i>Снятие флага 'Locked Out' на контроллере домена...</i>", parse_mode="HTML")
    await asyncio.sleep(1.5)

    await status_msg.delete()
    await message.answer(
        "✅ <b>Учетная запись разблокирована!</b>\n\n"
        "Теперь вы можете войти в систему. Если ошибка повторится, проверьте, не залипла ли клавиша CapsLock.",
        parse_mode="HTML",
        reply_markup=get_instant_actions_keyboard(),
    )


@router.message(InstantActionState.waiting_for_selection, F.text.contains("VPN"))
async def simulate_vpn_reset(message: types.Message):
    """Симуляция сброса VPN-сессии."""

    status_msg = await message.answer("📡 <i>Пинг шлюза удаленного доступа...</i>", parse_mode="HTML")
    await asyncio.sleep(1.0)

    await status_msg.edit_text("✂️ <i>Принудительное завершение зависшей сессии...</i>", parse_mode="HTML")
    await asyncio.sleep(1.5)

    await status_msg.edit_text("🔄 <i>Очистка кеша маршрутизации...</i>", parse_mode="HTML")
    await asyncio.sleep(1.0)

    await status_msg.delete()
    await message.answer(
        "✅ <b>Сессия сброшена.</b>\n\n"
        "Попробуйте подключиться к VPN заново через Cisco AnyConnect или OpenVPN. Доступ восстановлен.",
        parse_mode="HTML",
        reply_markup=get_instant_actions_keyboard(),
    )


# --- 3. Выход назад ---
@router.message(InstantActionState.waiting_for_selection, F.text == "🔙 Назад в меню")
async def back_to_main(message: types.Message, state: FSMContext):
    """Возврат в главное меню HelpDesk."""

    await state.clear()
    await message.answer("Вы вернулись в главное меню HelpDesk.", reply_markup=get_helpdesk_main_keyboard())


# --- Регистрация ---
def register_handlers(parent_router: Router):
    parent_router.include_router(router)

