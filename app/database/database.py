import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
from app.core.config import settings

# Загружаем переменные окружения
load_dotenv()

class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    pass

# URL для подключения
DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# Создаем синхронный движок с оптимизациями
engine = create_engine(
    DATABASE_URL,
    # echo=settings.DEBUG,  # Логировать SQL только в debug режиме
    poolclass=NullPool,  # Для избежания проблем с connection pool
    pool_pre_ping=True,  # Проверять соединение перед использованием
    pool_recycle=3600,  # Пересоздавать соединения каждый час
)

# Создаем синхронную фабрику сессий
SessionLocal = sessionmaker(
    engine,
    expire_on_commit=False,  # Объекты не expire после commit
    autoflush=False,
    autocommit=False,
)

def get_db():
    """
    Синхронная зависимость для получения сессии БД
    Использование:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """Создание всех таблиц (для инициализации)"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Удаление всех таблиц (для тестов)"""
    Base.metadata.drop_all(bind=engine)

# Утилиты для работы с БД
def get_sync_session():
    """Получить синхронную сессию (для ручного управления)"""
    return SessionLocal()