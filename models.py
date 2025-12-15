import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import BigInteger, Column, DateTime, Integer, func, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Загружаем переменные окружения из .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден в переменных окружения (.env)")

# Создаем движок SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)

# Базовый класс моделей
Base = declarative_base()

# Фабрика сессий
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class User(Base):
    """Модель пользователя Telegram.

    Поля:
    - id: внутренний PK
    - telegram_id: Telegram ID пользователя (уникальный)
    - started_at: время и дата старта бота для пользователя
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"<User id={self.id} telegram_id={self.telegram_id} started_at={self.started_at}>"


def init_db() -> None:
    """Создает таблицы в базе, если их еще нет."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Утилита для получения сессии (контекстный менеджер prefered в коде)."""
    return SessionLocal()


def ensure_user_started(session, telegram_id: int, started_at: datetime | None = None) -> User:
    """Идempotентно фиксирует старт пользователя.

    Если пользователь с таким telegram_id уже существует — вернёт его без изменений.
    Если нет — создаст запись с указанным started_at (или текущим временем на стороне БД).
    """
    from sqlalchemy import select

    user = session.execute(select(User).where(User.telegram_id == telegram_id)).scalar_one_or_none()
    if user:
        return user

    user = User(telegram_id=telegram_id)
    # Если явно передан started_at — зададим клиентское значение (иначе сработает server_default)
    if started_at is not None:
        user.started_at = started_at

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

