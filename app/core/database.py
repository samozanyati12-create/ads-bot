from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Создание асинхронного движка для продакшена
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Отключено логирование SQL
    poolclass=NullPool,  # Отключаем пулинг для Celery задач
    pool_pre_ping=True,  # Проверка соединений
    pool_recycle=3600,  # Пересоздание соединений каждый час
)

# Фабрика сессий
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False,  # Ручное управление флешем
    autocommit=False
)

# Получение сессии БД
async def get_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Создание таблиц
async def create_tables():
    from app.models.user import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Закрытие подключений при завершении
async def close_db():
    await engine.dispose()