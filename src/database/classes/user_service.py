from database.models import user
from database.models import Role_type, User_state
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exc
from sqlalchemy.dialects.postgresql import insert
from user_operation.schemas.databaseschemas import User
import logging

class UserService:
    @staticmethod
    async def is_user_connected(user_id:int, session:AsyncSession) -> bool:
        logging.info("Проверяем соединён ли пользователь с другим пользователем")
        result = None
        try:
            stmt_check_user = select(user.c.connected_user).where(user.c.id == user_id)
            result = await session.execute(stmt_check_user)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        result = result.all()
        if not bool(result):
            return False
        if result[0][0] == -1:
            return False
        return True

    @staticmethod
    async def get_user_from_db(user_id:int, session:AsyncSession):
        logging.info("Получаем пользователя из базы данных")
        result = None
        try:
            stmt_get_user = select(user).where(user.c.id == user_id)
            result = await session.execute(stmt_get_user)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        result = result.all()

        if bool(result):
            return result
    
    @staticmethod
    async def is_there_user(user_id:int, session:AsyncSession) -> bool:
        logging.info("Проверяем существование пользователя в базе данных")
        user = await UserService.get_user_from_db(user_id=user_id, session=session)
        return bool(user)

    @staticmethod
    async def get_connected_user_id(first_user_id:int, session:AsyncSession):
        logging.info("Получаем id присоединённого пользователя")
        user = await UserService.get_user_from_db(user_id=first_user_id, session=session)
        if bool(user):
            return user[0][3]

    @staticmethod
    async def get_username_with_user_id(user_id:int, session:AsyncSession):
        logging.info("Получаем имя ссылки пользователя")
        user = await UserService.get_user_from_db(user_id=user_id, session=session)
        if bool(user):
            return user[0][6]
    
    @staticmethod
    async def add_new_user(new_user:User, session:AsyncSession):
        logging.info("Добавляем нового пользователя в БД")

        try:
            stmt_add_new_user = insert(user).values(new_user.model_dump()).on_conflict_do_nothing(index_elements=['id']).returning(user.c.id)
            result = await session.execute(stmt_add_new_user)
        except exc.SQLAlchemyError as e:
            logging.error(e)

        if bool(result.all()):
            logging.debug("The user registered successfully")
            return {"status": "success"}
        else:
            logging.debug("The user wasn't register")
            return {"status": "failure"}
    
    @staticmethod
    async def update_field_connected_user(user_id:int, connected_user:int, session:AsyncSession):
        logging.info("Обновляем поле подключённого пользователя")
        
        try:
            stmt_update_connected_user = update(user).where(user.c.id == user_id).values(connected_user = connected_user)
            await session.execute(stmt_update_connected_user)
        except exc.SQLAlchemyError as e:
            logging.error(e)

    @staticmethod
    async def get_user_state(user_id:int, session:AsyncSession):
        logging.info("Получаем состояние пользователя")
        result = None
        try:
            stmt_check_user = select(user.c.state).where(user.c.id == user_id)
            result = await session.execute(stmt_check_user)
        except exc.SQLAlchemyError as e:
            logging.error(e)
            
        result = result.all()
        if bool(result):
            return result[0][0]

    @staticmethod
    async def change_user_state(user_id:int, session:AsyncSession, user_state:User_state):
        logging.info("Меняем состояние пользователя")
        try:
            stmt_update_user_state = update(user).where(user.c.id == user_id).values(state = user_state)
            await session.execute(stmt_update_user_state)
        except exc.SQLAlchemyError as e:
            logging.error(e)

    @staticmethod
    async def is_user_admin(user_id:int, session:AsyncSession) -> bool:
        logging.info("Проверяем является ли пользователь админом")
        result = None
        try:
            stmt_check_user = select(user).where(user.c.id == user_id).where(user.c.role_id == Role_type.admin)
            result = await session.execute(stmt_check_user)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        return bool(result.all())
    
    @staticmethod
    async def change_user_role(user_id:int, type_of_role:Role_type, session:AsyncSession):
        logging.info("Добавляем админа")
        try:
            stmt_change_role = update(user).where(user.c.id == user_id).values(role_id = type_of_role)
            await session.execute(stmt_change_role)
        except exc.SQLAlchemyError as e:
            logging.error(e)

    @staticmethod
    async def update_user_connected_user_and_chat_id(user_id:int, connected_user:int, chat_id:int, session:AsyncSession):
        logging.info("Обновляем информацию о подключённом пользователе и чате")
        try:
            stmt_update_user = update(user).where(user.c.id == user_id).values(connected_user = connected_user, prev_chat_id = chat_id)
            await session.execute(stmt_update_user)
        except exc.SQLAlchemyError as e:
            logging.error(e)

    @staticmethod
    async def get_current_chat(user_id:int, session:AsyncSession):
        logging.info("Получаем текущий чат")
        user = await UserService.get_user_from_db(user_id=user_id, session=session)
        if bool(user):
            return user[0][4]