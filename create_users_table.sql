-- SQL-запрос для создания таблицы users в PostgreSQL
-- Эта таблица уже автоматически создаётся через SQLAlchemy в models.py,
-- но если нужно создать вручную, используйте этот запрос:

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL UNIQUE,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Создание индексов для оптимизации запросов
CREATE INDEX IF NOT EXISTS ix_users_id ON users(id);
CREATE INDEX IF NOT EXISTS ix_users_telegram_id ON users(telegram_id);

-- Проверка созданной таблицы
SELECT * FROM users;

