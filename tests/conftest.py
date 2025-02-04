from typing import AsyncGenerator
from tests import prepare_test_database_service
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from database.database import get_async_session
from src.database.database import metadata
from src.config import (DB_HOST_TEST, DB_NAME_TEST, DB_PASS_TEST, DB_PORT_TEST,
                        DB_USER_TEST)
from src.main import app


# DATABASE
DATABASE_URL_TEST = f"postgresql+asyncpg://{DB_USER_TEST}:{DB_PASS_TEST}@{DB_HOST_TEST}:{DB_PORT_TEST}/{DB_NAME_TEST}"

engine_test = create_async_engine(DATABASE_URL_TEST, poolclass=NullPool)
async_session_maker = sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)
metadata.bind = engine_test

async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


@pytest.fixture(autouse=True, scope='session')
async def prepare_database():
    assert engine_test.url.database == 'test'

    async with engine_test.begin() as conn:
        await conn.run_sync(metadata.create_all)

    test_db_manager = prepare_test_database_service.TestDabaseManager()
    async for session in override_get_async_session():
        async with session.begin():
            await test_db_manager.prepare_database(session)

    yield
    
    async with engine_test.begin() as conn:
        await conn.run_sync(metadata.drop_all)

@pytest.fixture(scope="function")
async def db_session():
    async for session in override_get_async_session():
        async with session.begin():
            savepoint = await session.begin_nested()

            yield (session, savepoint)

            await session.rollback()