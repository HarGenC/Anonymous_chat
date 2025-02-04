import logging

from sqlalchemy import select, update, delete, exc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import punishment as punish
from user_operation.schemas.databaseschemas import Punishment
    
class PunishmentService:

    @staticmethod
    async def apply_punishment(session:AsyncSession, 
                                 punishment:Punishment):
        logging.info("Добавляем наказание для пользователя")

        punishment_id = None
        try:
            stmt_add_new_punishment = insert(punish).values(punishment.model_dump()).returning(punish.c.id)
            punishment_id = await session.execute(stmt_add_new_punishment)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        if not bool(punishment_id):
            return
        punishment_id = punishment_id.all()
        if bool(punishment_id):
            return punishment_id[0][0]
    
    @staticmethod
    async def delete_punishment_with_user_id(user_id:int, session:AsyncSession):
        logging.info("Удаляем наказание для определённого пользователя")
        punishment_id = None
        try:
            stmt_delete_punishment = delete(punish).where(punish.c.user_id == user_id)
            await session.execute(stmt_delete_punishment)
        except exc.SQLAlchemyError as e:
            logging.error(e)

    @staticmethod
    async def is_user_punished(user_id:int, session:AsyncSession) -> bool:
        logging.info("Проверяем наказан ли пользователь")
        result = None
        try:
            stmt_check_user = select(punish).where(punish.c.user_id == user_id)
            result = await session.execute(stmt_check_user)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        return bool(result.all())