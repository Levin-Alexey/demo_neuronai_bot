import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    Text,
    SmallInteger,
    ForeignKey,
    String,
    func,
    create_engine,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

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
    """Модель пользователя Telegram."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Связь с сессиями собеседований
    interview_sessions = relationship("InterviewSession", back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} telegram_id={self.telegram_id}>"

class CVReview(Base):
    __tablename__ = 'cv_reviews'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False)
    user_name = Column(String, nullable=True)
    file_id = Column(String, nullable=True)
    resume_text = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class InterviewSession(Base):
    """Сессия собеседования на позицию 'Менеджер по продажам'.

    Этапы (stage):
    - 0: старт, ждём ответ на вопрос 1
    - 1: ждём ответ на вопрос 2
    - 2: ждём ответ на вопрос 3
    - 3: завершено, есть рекомендация
    - -1: отменено

    hr_recommendation (JSONB):
    {
        "score": 7,
        "strengths": ["опыт в продажах", "коммуникабельность"],
        "concerns": ["нет опыта в B2B"],
        "verdict": "Рекомендован",
        "full_analysis": "Кандидат показал хорошие навыки..."
    }
    """

    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    telegram_id = Column(BigInteger, nullable=False, index=True)

    stage = Column(SmallInteger, default=0, nullable=False)

    # Вопросы (генерируются ИИ)
    q1 = Column(Text, nullable=True)
    q2 = Column(Text, nullable=True)
    q3 = Column(Text, nullable=True)

    # Ответы кандидата
    a1 = Column(Text, nullable=True)
    a2 = Column(Text, nullable=True)
    a3 = Column(Text, nullable=True)

    # ID голосовых сообщений (если отвечали голосом)
    voice_file_id_1 = Column(Text, nullable=True)
    voice_file_id_2 = Column(Text, nullable=True)
    voice_file_id_3 = Column(Text, nullable=True)

    # Рекомендация для HR-аналитика
    hr_recommendation = Column(JSONB, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Связь с пользователем
    user = relationship("User", back_populates="interview_sessions")

    def __repr__(self) -> str:
        return f"<InterviewSession id={self.id} tg={self.telegram_id} stage={self.stage}>"

    @property
    def is_active(self) -> bool:
        return self.completed_at is None and self.stage >= 0

    @property
    def is_completed(self) -> bool:
        return self.stage == 3 and self.completed_at is not None


# ==================== Инициализация БД ====================


def init_db() -> None:
    """Создает таблицы в базе, если их еще нет."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Получить сессию SQLAlchemy."""
    return SessionLocal()


# ==================== Функции для пользователей ====================
def save_cv_review(session, telegram_id, user_name, file_id, resume_text, ai_feedback, score=None):
    """
    Сохраняет результат проверки резюме в БД.
    """
    review = CVReview(
        telegram_id=telegram_id,
        user_name=user_name,
        file_id=file_id,
        resume_text=resume_text,
        ai_feedback=ai_feedback,
        score=score
    )
    session.add(review)
    session.commit()
    return review

def ensure_user_started(session, telegram_id: int, started_at: datetime | None = None) -> User:
    """Создать пользователя если не существует."""
    user = session.execute(select(User).where(User.telegram_id == telegram_id)).scalar_one_or_none()
    if user:
        return user

    user = User(telegram_id=telegram_id)
    if started_at is not None:
        user.started_at = started_at

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# ==================== Функции для собеседований ====================


def get_active_interview(session, telegram_id: int) -> InterviewSession | None:
    """Получить активную сессию собеседования."""
    return session.execute(
        select(InterviewSession)
        .where(InterviewSession.telegram_id == telegram_id)
        .where(InterviewSession.completed_at.is_(None))
        .where(InterviewSession.stage >= 0)
        .order_by(InterviewSession.started_at.desc())
    ).scalar_one_or_none()


def start_interview(session, telegram_id: int, first_question: str) -> InterviewSession:
    """Начать новое собеседование с первым вопросом.

    Args:
        session: SQLAlchemy сессия
        telegram_id: Telegram ID пользователя
        first_question: Первый вопрос от ИИ

    Returns:
        Новая сессия собеседования
    """
    # Отменяем старые активные сессии
    session.execute(
        update(InterviewSession)
        .where(InterviewSession.telegram_id == telegram_id)
        .where(InterviewSession.completed_at.is_(None))
        .values(completed_at=func.now(), stage=-1)
    )

    # Получаем user_id
    user = session.execute(select(User).where(User.telegram_id == telegram_id)).scalar_one_or_none()

    interview = InterviewSession(
        user_id=user.id if user else None,
        telegram_id=telegram_id,
        stage=0,
        q1=first_question,
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)
    return interview


def save_answer_1(
        session,
        telegram_id: int,
        answer: str,
        next_question: str,
        voice_file_id: str | None = None
) -> InterviewSession:
    """Сохранить ответ 1, записать вопрос 2, перейти на stage 1."""
    interview = get_active_interview(session, telegram_id)
    if not interview:
        raise ValueError("Нет активной сессии")

    interview.a1 = answer
    interview.voice_file_id_1 = voice_file_id
    interview.q2 = next_question
    interview.stage = 1

    session.commit()
    session.refresh(interview)
    return interview


def save_answer_2(
        session,
        telegram_id: int,
        answer: str,
        next_question: str,
        voice_file_id: str | None = None
) -> InterviewSession:
    """Сохранить ответ 2, записать вопрос 3, перейти на stage 2."""
    interview = get_active_interview(session, telegram_id)
    if not interview:
        raise ValueError("Нет активной сессии")

    interview.a2 = answer
    interview.voice_file_id_2 = voice_file_id
    interview.q3 = next_question
    interview.stage = 2

    session.commit()
    session.refresh(interview)
    return interview


def save_answer_3_and_complete(
        session,
        telegram_id: int,
        answer: str,
        hr_recommendation: dict,
        voice_file_id: str | None = None
) -> InterviewSession:
    """Сохранить ответ 3, записать рекомендацию HR, завершить собеседование."""
    interview = get_active_interview(session, telegram_id)
    if not interview:
        raise ValueError("Нет активной сессии")

    interview.a3 = answer
    interview.voice_file_id_3 = voice_file_id
    interview.hr_recommendation = hr_recommendation
    interview.stage = 3
    interview.completed_at = datetime.now()

    session.commit()
    session.refresh(interview)
    return interview


def cancel_interview(session, telegram_id: int) -> InterviewSession | None:
    """Отменить активное собеседование."""
    interview = get_active_interview(session, telegram_id)
    if not interview:
        return None

    interview.stage = -1
    interview.completed_at = datetime.now()

    session.commit()
    session.refresh(interview)
    return interview


def get_interview_history(session, telegram_id: int, limit: int = 10) -> list[InterviewSession]:
    """Получить историю собеседований пользователя."""
    return list(
        session.execute(
            select(InterviewSession)
            .where(InterviewSession.telegram_id == telegram_id)
            .where(InterviewSession.stage == 3)  # только завершённые
            .order_by(InterviewSession.completed_at.desc())
            .limit(limit)
        ).scalars().all()
    )


def get_all_completed_interviews(session, limit: int = 50) -> list[InterviewSession]:
    """Получить все завершённые собеседования (для HR-панели)."""
    return list(
        session.execute(
            select(InterviewSession)
            .where(InterviewSession.stage == 3)
            .order_by(InterviewSession.completed_at.desc())
            .limit(limit)
        ).scalars().all()
    )


# ==================== Проверка доступа ====================


def check_user_access(session, telegram_id: int) -> tuple[bool, datetime | None]:
    """Проверить, имеет ли пользователь доступ к боту (24 часа с момента started_at).
    
    Args:
        session: SQLAlchemy сессия
        telegram_id: Telegram ID пользователя
        
    Returns:
        tuple: (имеет_доступ: bool, дата_окончания_доступа: datetime | None)
    """
    from datetime import timedelta
    
    user = session.execute(
        select(User).where(User.telegram_id == telegram_id)
    ).scalar_one_or_none()
    
    if not user:
        return False, None
    
    # Доступ на 24 часа с момента started_at
    access_until = user.started_at + timedelta(hours=24)
    now = datetime.now(timezone.utc)
    
    has_access = now < access_until
    return has_access, access_until