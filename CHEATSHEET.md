# ⚡ Шпаргалка: Система контроля доступа

## 🚀 Быстрый старт

```bash
# Запуск бота
python main.py

# Запуск утилиты управления
python manage_access.py
```

## 📝 Основные концепции

- **24 часа** доступа с момента `/start`
- **Автоматическая** проверка при каждом действии
- **Middleware** блокирует доступ после истечения
- **UTC** для хранения, локальное время для отображения

## 🛠 Частые задачи

### Продлить доступ одному пользователю (SQL)
```sql
UPDATE users 
SET started_at = NOW() 
WHERE telegram_id = 123456789;
```

### Продлить доступ нескольким (SQL)
```sql
UPDATE users 
SET started_at = NOW() 
WHERE telegram_id IN (123456789, 987654321, 555555555);
```

### Проверить статус пользователя (SQL)
```sql
SELECT 
    telegram_id,
    started_at,
    started_at + INTERVAL '24 hours' as access_until,
    CASE 
        WHEN started_at + INTERVAL '24 hours' > NOW() THEN 'Активен'
        ELSE 'Истек'
    END as status
FROM users
WHERE telegram_id = 123456789;
```

### Получить активных пользователей (SQL)
```sql
SELECT COUNT(*) FROM users 
WHERE started_at + INTERVAL '24 hours' > NOW();
```

### Получить истекших пользователей (SQL)
```sql
SELECT COUNT(*) FROM users 
WHERE started_at + INTERVAL '24 hours' < NOW();
```

## 🐍 Python API

### Проверить доступ
```python
from models import get_session, check_user_access

with get_session() as session:
    has_access, access_until = check_user_access(session, 123456789)
    print(f"Доступ: {has_access}, До: {access_until}")
```

### Продлить доступ (через утилиту)
```python
from manage_access import extend_access

success = extend_access(123456789, hours=48)
print(f"Успешно: {success}")
```

### Получить информацию
```python
from manage_access import get_user_info

info = get_user_info(123456789)
print(info)
```

## ⚙️ Настройка

### Изменить период (models.py ~225)
```python
access_until = user.started_at + timedelta(hours=24)  # ← тут
```

### Изменить часовой пояс (main.py ~64, ~175)
```python
local_time = access_until + timedelta(hours=3)  # ← тут (MSK=3)
```

## 🧪 Тестирование

### Симулировать истечение доступа
```sql
UPDATE users 
SET started_at = NOW() - INTERVAL '25 hours' 
WHERE telegram_id = YOUR_ID;
```

### Вернуть нормальный доступ
```sql
UPDATE users 
SET started_at = NOW() 
WHERE telegram_id = YOUR_ID;
```

## 📊 Полезные запросы

### Топ 10 пользователей (по давности)
```sql
SELECT telegram_id, started_at 
FROM users 
ORDER BY started_at ASC 
LIMIT 10;
```

### Регистрации за сегодня
```sql
SELECT COUNT(*) 
FROM users 
WHERE DATE(started_at) = CURRENT_DATE;
```

### Истекает в ближайший час
```sql
SELECT telegram_id, 
       (started_at + INTERVAL '24 hours') - NOW() as time_left
FROM users
WHERE started_at + INTERVAL '24 hours' > NOW() 
  AND started_at + INTERVAL '24 hours' < NOW() + INTERVAL '1 hour'
ORDER BY time_left ASC;
```

## 📂 Документация

| Файл | Описание |
|------|----------|
| [ACCESS_CONTROL_README.md](ACCESS_CONTROL_README.md) | Полная документация |
| [QUICKSTART_ACCESS_CONTROL.md](QUICKSTART_ACCESS_CONTROL.md) | Быстрый старт |
| [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) | Что изменено |
| [MANAGE_ACCESS_README.md](MANAGE_ACCESS_README.md) | Утилита управления |
| [access_control_queries.sql](access_control_queries.sql) | SQL запросы |
| [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) | Статус реализации |

## 🔧 Решение проблем

### Middleware не работает
```python
# Проверьте в main.py:
dp.message.middleware(AccessCheckMiddleware())
```

### DATABASE_URL не найден
```bash
# Проверьте .env файл:
DATABASE_URL=postgresql+psycopg2://user:pass@host:port/db
```

### Пользователь не может войти
```sql
-- Проверьте доступ:
SELECT * FROM users WHERE telegram_id = 123456789;
```

## 💡 Советы

1. **Логирование**: Добавьте логи в middleware для отладки
2. **Мониторинг**: Настройте регулярные проверки активных пользователей
3. **Backup**: Делайте резервные копии БД перед массовыми изменениями
4. **Тестирование**: Проверяйте на тестовом аккаунте перед продакшеном

## 🎯 Команды утилиты

```
1 - Информация о пользователе
2 - Продлить доступ пользователю
3 - Продлить доступ нескольким
4 - Список активных
5 - Список истекших
6 - Выход
```

## 📞 Кнопки бота

- **🔄 Проверить доступ** - показать оставшееся время
- **👤 Связаться с менеджером** - форма обратной связи

---

**Быстрый доступ:** Сохраните этот файл в закладки!
