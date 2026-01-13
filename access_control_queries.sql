-- Полезные SQL запросы для управления системой доступа

-- ============================================================
-- ПРОСМОТР ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЯХ
-- ============================================================

-- 1. Все пользователи с информацией о доступе
SELECT 
    telegram_id,
    started_at,
    started_at + INTERVAL '24 hours' as access_until,
    CASE 
        WHEN started_at + INTERVAL '24 hours' > NOW() THEN 'Активен'
        ELSE 'Истек'
    END as status,
    CASE 
        WHEN started_at + INTERVAL '24 hours' > NOW() 
        THEN (started_at + INTERVAL '24 hours') - NOW()
        ELSE NOW() - (started_at + INTERVAL '24 hours')
    END as time_diff
FROM users
ORDER BY started_at DESC;

-- 2. Только активные пользователи (доступ не истек)
SELECT 
    telegram_id,
    started_at,
    started_at + INTERVAL '24 hours' as access_until,
    (started_at + INTERVAL '24 hours') - NOW() as time_left
FROM users
WHERE started_at + INTERVAL '24 hours' > NOW()
ORDER BY started_at DESC;

-- 3. Только пользователи с истекшим доступом
SELECT 
    telegram_id,
    started_at,
    started_at + INTERVAL '24 hours' as access_until,
    NOW() - (started_at + INTERVAL '24 hours') as expired_ago
FROM users
WHERE started_at + INTERVAL '24 hours' < NOW()
ORDER BY started_at DESC;

-- 4. Количество активных и неактивных пользователей
SELECT 
    CASE 
        WHEN started_at + INTERVAL '24 hours' > NOW() THEN 'Активные'
        ELSE 'Истекшие'
    END as status,
    COUNT(*) as count
FROM users
GROUP BY status;

-- 5. Пользователи, у которых доступ истекает в ближайший час
SELECT 
    telegram_id,
    started_at,
    started_at + INTERVAL '24 hours' as access_until,
    (started_at + INTERVAL '24 hours') - NOW() as time_left
FROM users
WHERE 
    started_at + INTERVAL '24 hours' > NOW() 
    AND started_at + INTERVAL '24 hours' < NOW() + INTERVAL '1 hour'
ORDER BY access_until ASC;

-- ============================================================
-- УПРАВЛЕНИЕ ДОСТУПОМ
-- ============================================================

-- 6. Продлить доступ конкретному пользователю (новые 24 часа с текущего момента)
-- ЗАМЕНИТЕ 123456789 на нужный telegram_id
UPDATE users 
SET started_at = NOW() 
WHERE telegram_id = 123456789;

-- 7. Продлить доступ всем пользователям с истекшим доступом
UPDATE users 
SET started_at = NOW() 
WHERE started_at + INTERVAL '24 hours' < NOW();

-- 8. Продлить доступ нескольким конкретным пользователям
-- ЗАМЕНИТЕ ID на нужные
UPDATE users 
SET started_at = NOW() 
WHERE telegram_id IN (123456789, 987654321, 555555555);

-- ============================================================
-- ТЕСТИРОВАНИЕ
-- ============================================================

-- 9. Симулировать истечение доступа для конкретного пользователя (для теста)
-- ЗАМЕНИТЕ 123456789 на ваш telegram_id для тестирования
UPDATE users 
SET started_at = NOW() - INTERVAL '25 hours' 
WHERE telegram_id = 123456789;

-- 10. Симулировать доступ, истекающий через 10 минут (для теста)
UPDATE users 
SET started_at = NOW() - INTERVAL '23 hours 50 minutes' 
WHERE telegram_id = 123456789;

-- 11. Вернуть нормальный доступ (24 часа с текущего момента)
UPDATE users 
SET started_at = NOW() 
WHERE telegram_id = 123456789;

-- ============================================================
-- СТАТИСТИКА И АНАЛИТИКА
-- ============================================================

-- 12. Статистика регистраций по дням
SELECT 
    DATE(started_at) as registration_date,
    COUNT(*) as users_count
FROM users
GROUP BY DATE(started_at)
ORDER BY registration_date DESC;

-- 13. Статистика регистраций за последние 7 дней
SELECT 
    DATE(started_at) as registration_date,
    COUNT(*) as users_count
FROM users
WHERE started_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(started_at)
ORDER BY registration_date DESC;

-- 14. Средняя продолжительность между регистрациями
SELECT 
    AVG(diff) as avg_time_between_registrations
FROM (
    SELECT 
        started_at - LAG(started_at) OVER (ORDER BY started_at) as diff
    FROM users
) as time_diffs
WHERE diff IS NOT NULL;

-- 15. Пользователи, которые зарегистрировались сегодня
SELECT 
    telegram_id,
    started_at,
    started_at + INTERVAL '24 hours' as access_until
FROM users
WHERE DATE(started_at) = CURRENT_DATE
ORDER BY started_at DESC;

-- ============================================================
-- ОЧИСТКА ДАННЫХ
-- ============================================================

-- 16. Удалить пользователей, доступ которых истек более 30 дней назад
-- ОСТОРОЖНО! Это удалит данные безвозвратно
-- DELETE FROM users 
-- WHERE started_at + INTERVAL '24 hours' < NOW() - INTERVAL '30 days';

-- 17. Посмотреть, сколько пользователей будет удалено (без удаления)
SELECT COUNT(*) as users_to_delete
FROM users 
WHERE started_at + INTERVAL '24 hours' < NOW() - INTERVAL '30 days';

-- ============================================================
-- ЭКСПОРТ ДАННЫХ
-- ============================================================

-- 18. Экспорт всех пользователей в CSV (запустите в psql с \copy)
-- \copy (SELECT telegram_id, started_at, started_at + INTERVAL '24 hours' as access_until FROM users) TO '/path/to/users_export.csv' WITH CSV HEADER;

-- ============================================================
-- МОНИТОРИНГ
-- ============================================================

-- 19. Пользователи, которые могут скоро обратиться (доступ истекает в ближайшие 3 часа)
SELECT 
    telegram_id,
    started_at,
    started_at + INTERVAL '24 hours' as access_until,
    EXTRACT(EPOCH FROM ((started_at + INTERVAL '24 hours') - NOW()))/3600 as hours_left
FROM users
WHERE 
    started_at + INTERVAL '24 hours' > NOW() 
    AND started_at + INTERVAL '24 hours' < NOW() + INTERVAL '3 hours'
ORDER BY access_until ASC;

-- 20. Топ 10 самых старых пользователей
SELECT 
    telegram_id,
    started_at,
    NOW() - started_at as account_age
FROM users
ORDER BY started_at ASC
LIMIT 10;

-- ============================================================
-- СОЗДАНИЕ ПРЕДСТАВЛЕНИЙ (VIEWS)
-- ============================================================

-- 21. Создать представление для быстрого доступа к активным пользователям
CREATE OR REPLACE VIEW active_users AS
SELECT 
    telegram_id,
    started_at,
    started_at + INTERVAL '24 hours' as access_until,
    (started_at + INTERVAL '24 hours') - NOW() as time_left
FROM users
WHERE started_at + INTERVAL '24 hours' > NOW();

-- 22. Создать представление для пользователей с истекшим доступом
CREATE OR REPLACE VIEW expired_users AS
SELECT 
    telegram_id,
    started_at,
    started_at + INTERVAL '24 hours' as access_until,
    NOW() - (started_at + INTERVAL '24 hours') as expired_ago
FROM users
WHERE started_at + INTERVAL '24 hours' < NOW();

-- Использование представлений:
-- SELECT * FROM active_users;
-- SELECT * FROM expired_users;

-- ============================================================
-- ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ
-- ============================================================

-- 23. Создать индекс для быстрого поиска по времени доступа
-- (Полезно, если пользователей много)
CREATE INDEX IF NOT EXISTS idx_users_started_at ON users(started_at);

-- 24. Проверить использование индексов
-- EXPLAIN ANALYZE SELECT * FROM users WHERE started_at + INTERVAL '24 hours' > NOW();
