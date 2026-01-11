"""Определение состояний FSM для управления потоком диалога."""

from aiogram.fsm.state import State, StatesGroup


class BotStates(StatesGroup):
    """Состояния бота для управления навигацией по разделам."""

    # Главное меню
    MAIN_MENU = State()

    # HR и найм
    HR_MENU = State()
    INTERVIEW = State()  # Пользователь проходит собеседование
    CV_SCAN = State()  # Пользователь отправляет резюме для анализа
    QUICK_SEARCH = State()  # Быстрый подбор кандидатов
    HR_INFO = State()  # Информация для HR

    # IT HelpDesk
    IT_HELPDESK_MENU = State()
    AI_EYE = State()  # AI-Глаз - анализ скриншотов
    INSTANT_ACTION = State()  # Мгновенное действие
    SMART_TICKET = State()  # Умный тикет
    HOW_TO_CONNECT = State()  # Как подключить

    # Охрана труда
    LABOR_SAFETY_MENU = State()
    PHOTO_CONTROL = State()  # Фото-контроль для получения допуска
    WORK_PERMIT = State()  # Оформление работ
    REPORT_VIOLATION = State()  # Сообщение о нарушении
    BOT_INSTRUCTOR = State()  # Бот-инструктор

    # База знаний
    KNOWLEDGE_BASE_MENU = State()

    # AI-Менеджер
    AI_MANAGER_MENU = State()
    MANAGER_CONTACT = State()  # Состояние ожидания сообщения для менеджера
