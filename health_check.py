#!/usr/bin/env python3
"""
Быстрая проверка системы доступа.
Запустите этот скрипт для диагностики проблем.
"""

import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

print("🔍 СИСТЕМА ДИАГНОСТИКИ ДОСТУПА\n")
print("="*60)

# Проверка 1: .env файл
print("\n1️⃣  Проверка .env файла...")
load_dotenv()

if os.getenv('BOT_TOKEN'):
    print("   ✅ BOT_TOKEN найден")
else:
    print("   ❌ BOT_TOKEN не найден!")

if os.getenv('DATABASE_URL'):
    print("   ✅ DATABASE_URL найден")
else:
    print("   ❌ DATABASE_URL не найден!")

# Проверка 2: Подключение к БД
print("\n2️⃣  Проверка подключения к БД...")
try:
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker
    from models import User
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        result = session.execute(select(User)).scalars().first()
    
    print("   ✅ Подключение к БД успешно")
    
except Exception as e:
    print(f"   ❌ Ошибка подключения: {e}")
    exit(1)

# Проверка 3: Таблица users
print("\n3️⃣  Проверка таблицы users...")
try:
    with SessionLocal() as session:
        count = len(session.execute(select(User)).scalars().all())
    print(f"   ✅ Таблица users существует ({count} записей)")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# Проверка 4: Функция check_user_access
print("\n4️⃣  Проверка функции check_user_access...")
try:
    from models import check_user_access
    
    with SessionLocal() as session:
        # Берем первого пользователя
        user = session.execute(select(User)).scalars().first()
        
        if user:
            has_access, access_until = check_user_access(
                session, user.telegram_id)
            print(f"   ✅ Функция работает")
            print(f"      Пользователь {user.telegram_id}:")
            print(f"      - Доступ: {'АКТИВЕН' if has_access else 'ИСТЕК'}")
            print(f"      - access_until: {access_until}")
        else:
            print("   ⚠️  Нет пользователей в БД для проверки")

except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

# Проверка 5: main.py
print("\n5️⃣  Проверка main.py...")
try:
    with open('main.py', 'r') as f:
        content = f.read()
    
    if 'class AccessCheckMiddleware' in content:
        print("   ✅ AccessCheckMiddleware определена")
    else:
        print("   ❌ AccessCheckMiddleware не найдена!")
    
    if 'dp.message.middleware(AccessCheckMiddleware())' in content:
        print("   ✅ Middleware зарегистрирована")
    else:
        print("   ❌ Middleware не зарегистрирована!")
    
    if '[ACCESS CHECK]' in content:
        print("   ✅ Логирование добавлено")
    else:
        print("   ⚠️  Логирование не найдено (добавьте для отладки)")

except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# Проверка 6: models.py
print("\n6️⃣  Проверка models.py...")
try:
    with open('models.py', 'r') as f:
        content = f.read()
    
    if 'def check_user_access' in content:
        print("   ✅ Функция check_user_access определена")
    else:
        print("   ❌ Функция check_user_access не найдена!")
    
    if 'timedelta(hours=24)' in content:
        print("   ✅ Проверка 24 часов найдена")
    else:
        print("   ⚠️  Проверка 24 часов не найдена!")

except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\n" + "="*60)
print("\n✨ ДИАГНОСТИКА ЗАВЕРШЕНА\n")

# Рекомендации
print("💡 РЕКОМЕНДАЦИИ:")
print("1. Если все ✅ - система должна работать")
print("2. Если есть ❌ - проверьте указанные файлы")
print("3. Запустите: python debug_access.py [TELEGRAM_ID]")
print("   для подробной отладки конкретного пользователя")
print("\n📖 Полная инструкция: DEBUGGING_ACCESS.md")
