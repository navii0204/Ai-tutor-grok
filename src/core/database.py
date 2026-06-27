"""Async SQLAlchemy database engine + session factory.

Scalability note: To migrate from SQLite → Postgres, change DATABASE_URL
in .env.  For horizontal scaling, use a connection pool (AsyncPG + pgbouncer).
For read replicas, inject a separate read-engine per request.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedColumn, mapped_column
from sqlalchemy import String, DateTime
from datetime import datetime, timezone

from src.core.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


_engine: Any = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> Any:
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args: dict[str, Any] = {}
        if "sqlite" in settings.db.database_url:
            connect_args["check_same_thread"] = False
        _engine = create_async_engine(
            settings.db.database_url,
            echo=settings.app_debug,
            connect_args=connect_args,
            # Scalability: For Postgres, set pool_size=20, max_overflow=40
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async DB session per request."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_all_tables() -> None:
    """Create all tables. Called once at startup (use Alembic for prod migrations)."""
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
