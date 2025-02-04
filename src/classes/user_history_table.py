import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, Table, TIMESTAMP, Enum, ForeignKey, exc
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from user_operation.schemas.databaseschemas import User_state, UserMessageHistory
from database import models
from database.models import user


class UserHistoryTableManager():
    user_history_table:Table
    user_id:int
    
    def __init__ (self, user_id:int):
        table_name = "history_user_" + str(user_id)

        self.user_id = user_id
        self.user_history_table = Table(
        table_name, models.metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("user_id", Integer, ForeignKey("public.user.id")),
        Column("time_sended_message", TIMESTAMP, nullable=False),
        Column("file_id", String, nullable=True),
        Column("text", String, nullable=True),
        Column("state", Enum(models.User_state), default=0),
        Column("chat_id", Integer, nullable=True),
        schema='history',
        extend_existing=True
        )

    async def add_message_in_history(self, state:User_state, chat_id:int, session:AsyncSession, user_id:int, file_id:str = "None", text:str = "None"):
        logging.info("Добавляем сообщение в историю")
        new_user_message = None
        new_user_message_id = None
        try:
            new_user_message = UserMessageHistory(
                user_id = user_id,
                time_sended_message=datetime.utcnow(),
                file_id=file_id,
                text=str(text),
                state=state,
                chat_id = chat_id
            )
        except Exception as e:
            logging.error(e)

        try:
            stmt_add_new_user_message = insert(self.user_history_table).values(new_user_message.model_dump()).returning(self.user_history_table.c.id)
            new_user_message_id = await session.execute(stmt_add_new_user_message)
        except exc.SQLAlchemyError as e:
            print(e)
            logging.error(e)
        return new_user_message_id.scalar_one()
    
    async def get_user_history_in_chat(self, chat_id:int, session:AsyncSession):
        result = None
        try:
            stmt_get_chat_history = select(self.user_history_table, user.c.username).where(self.user_history_table.c.chat_id == chat_id).where(self.user_history_table.c.state == User_state.chatting_state).join(user, user.c.id == self.user_history_table.c.user_id)
            result = await session.execute(stmt_get_chat_history)
        except exc.SQLAlchemyError as e:
            logging.error(e)
            
        return result.all()

