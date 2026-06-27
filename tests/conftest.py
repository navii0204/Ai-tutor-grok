"""Shared pytest fixtures for all tests."""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.database import Base
from src.core.student_model.models import HolisticMarkers, StudentProfile
from src.core.student_model.repository import StudentRepository
from src.core.student_model.service import StudentModelService

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(bind=async_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_llm() -> AsyncMock:
    llm = AsyncMock()
    llm.chat = AsyncMock(
        return_value=(
            "That's an interesting observation! What do you think would happen "
            "if you changed one variable at a time? What makes you say that?"
        )
    )
    llm.health_check = AsyncMock(return_value=True)
    return llm


@pytest.fixture
def student_service(db_session: AsyncSession) -> StudentModelService:
    return StudentModelService(db_session, "test-tenant")
