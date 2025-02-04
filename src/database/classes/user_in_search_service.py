
from database.models import user_in_search
from database.models import User_filter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, exc
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from user_operation.schemas.databaseschemas import UserInSearch
import logging

class UserInSearchService:
    @staticmethod
    async def add_user_in_search(new_user_in_search:UserInSearch, session:AsyncSession) -> int:
        logging.info("Добавляем пользователя в поиск")
        user_in_search_id = None
        try:
            stmt_add_user_in_search = insert(user_in_search).values(new_user_in_search.model_dump()).returning(user_in_search.c.id)
            user_in_search_id = await session.execute(stmt_add_user_in_search)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        if not bool(user_in_search_id):
            return
        user_in_search_id = user_in_search_id.all()
        if bool(user_in_search_id):
            return user_in_search_id[0][0]

    @staticmethod
    async def find_first_user_in_search(session:AsyncSession, filter: User_filter = User_filter.all):
        logging.info("Ищем первого попавшегося пользователя в поиске")
        result = None
        try:
            stmt_check_user = select(user_in_search.c.user_id).where(user_in_search.c.filter == filter)
            result = await session.execute(stmt_check_user)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        user_row = result.fetchone()
        if user_row == None:
            return None
        else:
            return user_row[0]

    @staticmethod
    async def delete_user_in_search(user_id:int, session:AsyncSession):
        logging.info("Удаляем пользователя из поиска")
        try:
            stmt_delete_user_in_search = delete(user_in_search).where(user_in_search.c.user_id == user_id)
            await session.execute(stmt_delete_user_in_search)
        except exc.SQLAlchemyError as e:
            logging.error(e)

    @staticmethod
    async def get_user_in_search_with_the_longest_time(session:AsyncSession):
        logging.info("Ищем пользователя в поиске с самым длинным временем ожидания")
        result = None
        try:
            stmt_get_chatgpt_person = select(user_in_search).order_by(user_in_search.c.started_at.desc())
            result = await session.execute(stmt_get_chatgpt_person)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        return result.fetchone()