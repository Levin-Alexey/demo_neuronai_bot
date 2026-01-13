"""
Скрипт для отладки и проверки системы контроля доступа.
"""

import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from models import User

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден в .env файле")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def check_user_debug(telegram_id: int):
    """Проверить доступ пользователя с детальным логированием."""
    print(f"\n{'='*60}")
    print(f"🔍 ОТЛАДКА ДОСТУПА ДЛЯ ПОЛЬЗОВАТЕЛЯ {telegram_id}")
    print(f"{'='*60}")
    
    with SessionLocal() as session:
        user = session.execute(
            select(User).where(User.telegram_id == telegram_id)
        ).scalar_one_or_none()
        
        if not user:
            print("❌ Пользователь не найден в БД!")
            return
        
        print(f"✅ Пользователь найден в БД")
        print(f"   ID: {user.id}")
        print(f"   Telegram ID: {user.telegram_id}")
        
        # Проверяем started_at
        started_at = user.started_at
        print(f"\n📅 Информация о started_at:")
        print(f"   Значение: {started_at}")
        print(f"   Тип: {type(started_at)}")
        print(f"   Timezone: {started_at.tzinfo if hasattr(started_at, 'tzinfo') else 'None'}")
        
        # Вычисляем access_until
        access_until = started_at + timedelta(hours=24)
        print(f"\n⏰ Вычисленный доступ:")
        print(f"   access_until: {access_until}")
        print(f"   Timezone: {access_until.tzinfo}")
        
        # Получаем текущее время
        now = datetime.now(timezone.utc)
        print(f"\n🕐 Текущее время (UTC):")
        print(f"   NOW(): {now}")
        print(f"   Timezone: {now.tzinfo}")
        
        # Сравнение
        print(f"\n📊 СРАВНЕНИЕ:")
        print(f"   NOW() < access_until? {now < access_until}")
        print(f"   Разница: {access_until - now}")
        
        if now < access_until:
            hours = int((access_until - now).total_seconds() / 3600)
            minutes = int(((access_until - now).total_seconds() % 3600) / 60)
            print(f"   ✅ ДОСТУП АКТИВЕН (осталось {hours}ч {minutes}м)")
        else:
            hours = int((now - access_until).total_seconds() / 3600)
            minutes = int(((now - access_until).total_seconds() % 3600) / 60)
            print(f"   ❌ ДОСТУП ИСТЕК ({hours}ч {minutes}м назад)")
        
        # Дополнительная информация
        print(f"\n💾 ИНФОРМАЦИЯ ДЛЯ АДМИНИСТРАТОРА:")
        print(f"   started_at (для копирования в SQL):")
        print(f"   {started_at}")
        print(f"\n   Чтобы продлить доступ, выполните:")
        print(f"   UPDATE users SET started_at = NOW() WHERE telegram_id = {telegram_id};")
        print(f"\n   Чтобы установить started_at на -2 дня:")
        print(f"   UPDATE users SET started_at = NOW() - INTERVAL '2 days' ")
        print(f"   WHERE telegram_id = {telegram_id};")
        print(f"\n{'='*60}\n")


if __name__ == "__main__":
    # Получить ID пользователя
    try:
        tid = int(input("Введите Telegram ID для проверки: "))
        check_user_debug(tid)
    except ValueError:
        print("❌ Некорректный ID")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
