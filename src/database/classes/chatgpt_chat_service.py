
from database.models import chatgpt_chat
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc
from sqlalchemy.dialects.postgresql import insert
from user_operation.schemas.databaseschemas import ChatGPTPerson
import logging

class ChatgptChatService:
    
    @staticmethod
    async def get_chatgpt_person(user_id:int, chat_id:int, session:AsyncSession):
        logging.info("Получаем личность чатГПТ")
        result = None
        try:
            stmt_get_chatgpt_person = select(chatgpt_chat.c.chatgpt_person).where(chatgpt_chat.c.user_id == user_id).where(chatgpt_chat.c.chat_id == chat_id)
            result = await session.execute(stmt_get_chatgpt_person)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        if not bool(result):
            return
        result = result.all()
        if bool(result):
            return result[0][0]

    @staticmethod
    async def add_chatgpt_person(chatgpt_person:ChatGPTPerson, session:AsyncSession):
        logging.info("Добавляем личность чатГПТ")
        chatgpt_person_id = None
        try:
            stmt_add_new_chatgpt_person = insert(chatgpt_chat).values(chatgpt_person.model_dump()).returning(chatgpt_chat.c.id)
            chatgpt_person_id = await session.execute(stmt_add_new_chatgpt_person)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        if bool(chatgpt_person_id):
            chatgpt_person_id = chatgpt_person_id.all()
            return chatgpt_person_id[0][0]
    