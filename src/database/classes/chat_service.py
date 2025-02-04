import logging
import datetime
import time
from sqlalchemy import select, update, case, exc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import chat, user, report
from user_operation.schemas.databaseschemas import Chat

class ChatService:
    @staticmethod
    async def add_new_chat(new_chat:Chat, session:AsyncSession) -> int:
        logging.info("Добавляем новый чат в БД")
        new_chat = new_chat.model_dump()
        new_chat["finished_at"] = None
        chat_id = None
        try:
            stmt_add_new_chat = insert(chat).values(new_chat).returning(chat.c.id)
            chat_id = await session.execute(stmt_add_new_chat)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        if not bool(chat_id):
            return
        chat_id = chat_id.all()
        if bool(chat_id):
            return chat_id[0][0]

    @staticmethod
    async def set_finish_time_for_user_chat(user_id:int, finished_at:datetime, session:AsyncSession):
        logging.info("Обновляем поле времени завершения чата")
        try:
            stmt_update_chat_info = (
            update(chat)
            .where(chat.c.id == select(user.c.prev_chat_id).where(user.c.id == user_id).scalar_subquery())
            .values(finished_at = finished_at)
            )
            await session.execute(stmt_update_chat_info)
        except exc.SQLAlchemyError as e:
            logging.error(e)

    @staticmethod
    async def get_reported_user(report_id:int, session:AsyncSession): # Думаю эту функцию нужно переделать с помощью join
        logging.info("Получаем id пользователя, на которого пожаловались")
        result = None

        try:
            query = (
            select(
                case(
            # Если жалобщик первый пользователь, то жалоба на второго
            (report.c.user_id == chat.c.first_user_id, chat.c.second_user_id),
            # Если жалобщик второй пользователь, то жалоба на первого
            (report.c.user_id == chat.c.second_user_id, chat.c.first_user_id),
        ).label("reported_user_id")  # Присваиваем алиас для результата
        ).where(chat.c.id == select(report.c.chat_id).where(report.c.id == report_id).scalar_subquery())
            .outerjoin(report, chat.c.id == report.c.chat_id)
            .where(report.c.id == report_id)
        )
            result = await session.execute(query)
        except exc.SQLAlchemyError as e:
            print("ОШИБКА")
            logging.error(e)

        result = result.all()
        
        if bool(result):
           return result[0][0]