"""
Database connection and session management
SQLAlchemy async setup for PostgreSQL
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import structlog

from config import settings

logger = structlog.get_logger()

# Create the SQLAlchemy engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    poolclass=NullPool,   # Use NullPool for simplicity in single-container setup
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create the declarative base
metadata = MetaData()
Base = declarative_base(metadata=metadata)


async def init_db():
    """
    Initialize database - create tables if they don't exist
    """
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they are registered
            from .models import Incident, Action, Setting
            
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    Used with FastAPI's Depends()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions
    Use when you need manual session management
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database transaction error", error=str(e))
            raise
        finally:
            await session.close()


async def close_db():
    """
    Close database connections
    Call this during application shutdown
    """
    await engine.dispose()
    logger.info("Database connections closed")
