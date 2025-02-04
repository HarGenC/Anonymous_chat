from typing import AsyncGenerator


from sqlalchemy import Column, Integer, String, MetaData, Table, TIMESTAMP, Enum, ForeignKey, exc
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER
from database import models

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base = declarative_base()

metadata = MetaData()

engine = create_async_engine(DATABASE_URL)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def add_new_user_history_table(user_id:int):
    logging.info("Создание таблицы истории пользователя")
    table_name = "history_user_" + str(user_id)

    user_table = Table(
        table_name, models.metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("user_id", Integer, ForeignKey("user.id")),
        Column("time_sended_message", TIMESTAMP, nullable=False),
        Column("file_id", String, nullable=True),
        Column("text", String, nullable=True),
        Column("state", Enum(models.User_state), default=0),
        Column("chat_id", Integer, nullable=True),
        schema='history',
        extend_existing=True
        )
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(models.metadata.create_all)
    except exc.SQLAlchemyError as e:
        logging.error(e)