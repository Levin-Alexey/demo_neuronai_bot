"""
Утилита для управления доступом пользователей к боту.
Позволяет администратору легко продлевать доступ пользователям.
"""

import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from models import User

# Загружаем переменные окружения
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден в .env файле")

# Создаем подключение к БД
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_user_info(telegram_id: int) -> dict | None:
    """Получить информацию о пользователе."""
    with SessionLocal() as session:
        user = session.execute(
            select(User).where(User.telegram_id == telegram_id)
        ).scalar_one_or_none()
        
        if not user:
            return None
        
        access_until = user.started_at + timedelta(hours=24)
        now = datetime.now(timezone.utc)
        has_access = now < access_until
        
        return {
            "telegram_id": user.telegram_id,
            "started_at": user.started_at,
            "access_until": access_until,
            "has_access": has_access,
            "time_left": access_until - now if has_access else None,
            "expired_ago": now - access_until if not has_access else None
        }


def extend_access(telegram_id: int, hours: int = 24) -> bool:
    """
    Продлить доступ пользователю.
    
    Args:
        telegram_id: Telegram ID пользователя
        hours: Количество часов доступа (по умолчанию 24)
    
    Returns:
        True если успешно, False если пользователь не найден
    """
    with SessionLocal() as session:
        user = session.execute(
            select(User).where(User.telegram_id == telegram_id)
        ).scalar_one_or_none()
        
        if not user:
            return False
        
        user.started_at = datetime.now(timezone.utc)
        session.commit()
        return True


def extend_access_multiple(telegram_ids: list[int], hours: int = 24) -> dict:
    """
    Продлить доступ нескольким пользователям.
    
    Args:
        telegram_ids: Список Telegram ID
        hours: Количество часов доступа
    
    Returns:
        Словарь со статистикой: {"success": [], "failed": []}
    """
    result = {"success": [], "failed": []}
    
    for tid in telegram_ids:
        if extend_access(tid, hours):
            result["success"].append(tid)
        else:
            result["failed"].append(tid)
    
    return result


def get_active_users() -> list[dict]:
    """Получить список всех активных пользователей."""
    with SessionLocal() as session:
        users = session.execute(select(User)).scalars().all()
        
        active_users = []
        now = datetime.now(timezone.utc)
        
        for user in users:
            access_until = user.started_at + timedelta(hours=24)
            if now < access_until:
                active_users.append({
                    "telegram_id": user.telegram_id,
                    "started_at": user.started_at,
                    "access_until": access_until,
                    "time_left": access_until - now
                })
        
        return active_users


def get_expired_users() -> list[dict]:
    """Получить список всех пользователей с истекшим доступом."""
    with SessionLocal() as session:
        users = session.execute(select(User)).scalars().all()
        
        expired_users = []
        now = datetime.now(timezone.utc)
        
        for user in users:
            access_until = user.started_at + timedelta(hours=24)
            if now >= access_until:
                expired_users.append({
                    "telegram_id": user.telegram_id,
                    "started_at": user.started_at,
                    "access_until": access_until,
                    "expired_ago": now - access_until
                })
        
        return expired_users


def print_user_info(user_info: dict) -> None:
    """Красиво вывести информацию о пользователе."""
    if not user_info:
        print("❌ Пользователь не найден")
        return
    
    print(f"\n📊 Информация о пользователе {user_info['telegram_id']}")
    print(f"   Начало доступа: {user_info['started_at']}")
    print(f"   Конец доступа:  {user_info['access_until']}")
    
    if user_info['has_access']:
        hours = int(user_info['time_left'].total_seconds() / 3600)
        minutes = int((user_info['time_left'].total_seconds() % 3600) / 60)
        print(f"   ✅ Статус: АКТИВЕН")
        print(f"   ⏰ Осталось: {hours} ч. {minutes} мин.")
    else:
        hours = int(user_info['expired_ago'].total_seconds() / 3600)
        minutes = int((user_info['expired_ago'].total_seconds() % 3600) / 60)
        print(f"   ❌ Статус: ИСТЕК")
        print(f"   ⏰ Истек назад: {hours} ч. {minutes} мин.")
    print()


# ============================================================
# ИНТЕРАКТИВНОЕ МЕНЮ
# ============================================================

def main_menu():
    """Главное интерактивное меню."""
    while True:
        print("\n" + "="*60)
        print("🤖 УПРАВЛЕНИЕ ДОСТУПОМ К БОТУ")
        print("="*60)
        print("1. 👤 Информация о пользователе")
        print("2. ⏰ Продлить доступ пользователю")
        print("3. 👥 Продлить доступ нескольким пользователям")
        print("4. ✅ Список активных пользователей")
        print("5. ❌ Список пользователей с истекшим доступом")
        print("6. 🚪 Выход")
        print("="*60)
        
        choice = input("\nВыберите действие (1-6): ").strip()
        
        if choice == "1":
            telegram_id = input("Введите Telegram ID: ").strip()
            try:
                user_info = get_user_info(int(telegram_id))
                print_user_info(user_info)
            except ValueError:
                print("❌ Некорректный ID")
        
        elif choice == "2":
            telegram_id = input("Введите Telegram ID: ").strip()
            hours = input("Количество часов (по умолчанию 24): ").strip()
            hours = int(hours) if hours else 24
            
            try:
                if extend_access(int(telegram_id), hours):
                    print(f"✅ Доступ продлен на {hours} часов")
                    user_info = get_user_info(int(telegram_id))
                    print_user_info(user_info)
                else:
                    print("❌ Пользователь не найден")
            except ValueError:
                print("❌ Некорректные данные")
        
        elif choice == "3":
            ids_str = input(
                "Введите Telegram ID через запятую: "
            ).strip()
            hours = input("Количество часов (по умолчанию 24): ").strip()
            hours = int(hours) if hours else 24
            
            try:
                telegram_ids = [
                    int(tid.strip()) for tid in ids_str.split(",")
                ]
                result = extend_access_multiple(telegram_ids, hours)
                
                print(f"\n✅ Успешно продлено: {len(result['success'])} польз.")
                if result['success']:
                    print(f"   ID: {result['success']}")
                
                print(f"\n❌ Не найдено: {len(result['failed'])} польз.")
                if result['failed']:
                    print(f"   ID: {result['failed']}")
            except ValueError:
                print("❌ Некорректные данные")
        
        elif choice == "4":
            active = get_active_users()
            print(f"\n✅ Активных пользователей: {len(active)}")
            
            for user in active[:10]:  # Показываем первых 10
                hours = int(user['time_left'].total_seconds() / 3600)
                minutes = int(
                    (user['time_left'].total_seconds() % 3600) / 60
                )
                print(
                    f"   {user['telegram_id']}: "
                    f"осталось {hours}ч {minutes}м"
                )
            
            if len(active) > 10:
                print(f"   ... и еще {len(active) - 10} пользователей")
        
        elif choice == "5":
            expired = get_expired_users()
            print(f"\n❌ Пользователей с истекшим доступом: {len(expired)}")
            
            for user in expired[:10]:  # Показываем первых 10
                hours = int(user['expired_ago'].total_seconds() / 3600)
                print(
                    f"   {user['telegram_id']}: "
                    f"истек {hours}ч назад"
                )
            
            if len(expired) > 10:
                print(f"   ... и еще {len(expired) - 10} пользователей")
        
        elif choice == "6":
            print("\n👋 До свидания!")
            break
        
        else:
            print("\n❌ Некорректный выбор")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Программа прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
