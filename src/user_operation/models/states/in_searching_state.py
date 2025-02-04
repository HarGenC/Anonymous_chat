import logging
import telebot
from datetime import datetime
from database.classes import chat_service, user_in_search_service, user_service
from user_operation.models.states.current_state import *
from database.database import get_async_session
from user_operation.models.states import chatting_state
from user_operation.models.states import menu_state
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from database.models import User_filter, User_state
from user_operation.models import user_state_machine as usm
from sqlalchemy.ext.asyncio import AsyncSession
from user_operation.schemas.databaseschemas import Chat, UserInSearch

class InSearchingState(CurrentState):
    def __init__(self):
        super().__init__()
        self.register_commands()

    async def enter_state(self, user_manager:usm.UserStateManager):
        logging.info("Пользователь вошёл в состояние поиска")
        user_id = None
        async for session in get_async_session():
            user_id = await user_in_search_service.UserInSearchService.find_first_user_in_search(session=session)
        if user_id == None:
            async for session in get_async_session():
                async with session.begin():
                    new_user_in_search = None
                    try:
                        new_user_in_search = UserInSearch(
                            user_id = user_manager.message.from_user.id,
                            started_at = datetime.utcnow(),
                            filter = User_filter.all
                        )
                    except Exception as e:
                        logging.error(e)
                    await user_in_search_service.UserInSearchService.add_user_in_search(new_user_in_search=new_user_in_search, session=session)
                    await user_service.UserService.change_user_state(user_id=user_manager.message.from_user.id, session=session, user_state=User_state.in_searching_state)
                    try:
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, text="Начат поиск...", reply_markup=self.create_user_searching_keyboard())
                    except telebot.apihelper.ApiException as e:
                        logging.error(e)
        else:
            async for session in get_async_session():
                async with session.begin():
                    await self.connect_two_users(first_user_id=user_manager.message.from_user.id, second_user_id=user_id, session=session)
            await user_manager.switch_state(current_state=chatting_state.ChattingState())
            try:
                await user_manager.bot.send_message(chat_id=user_id, text="Найден собеседник, приятного вам общения", reply_markup=user_manager.current_state.create_user_started_chat_keyboard())
            except telebot.apihelper.ApiException as e:
                logging.error(e)
        
    def create_user_searching_keyboard(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Прекратить поиск"))
        return markup

    async def update_state(self, user_manager:usm.UserStateManager):
        if user_manager.message.text in self.commands:
            await self.commands.get(user_manager.message.text)(user_manager)

    async def is_state(self):
        return User_state.in_searching_state

    def register_commands(self):
        # Регистрация команд через вызов декоратора
        self.command("Прекратить поиск")(self.finish_searching)

    async def finish_searching(self, user_manager:usm.UserStateManager):
        logging.info("Пользователь закончил поиск")
        async for session in get_async_session():
            async with session.begin():
                await user_in_search_service.UserInSearchService.delete_user_in_search(user_id=user_manager.message.from_user.id, session=session)
                await user_service.UserService.change_user_state(user_id=user_manager.message.from_user.id, session=session, user_state=User_state.menu_state)
                await user_manager.switch_state(current_state=menu_state.MenuState())
    
    
    async def connect_two_users(self, first_user_id:int, second_user_id:int, session:AsyncSession):
        logging.info("Соединяем двух пользователей")
        
        time = datetime.utcnow()
        new_chat = None
        try:
            new_chat = Chat(
                first_user_id = first_user_id,
                second_user_id = second_user_id,
                started_at = time,
                history_path = "_".join([str(first_user_id), str(second_user_id), str(time)])
            )
        except Exception as e:
            logging.error(e) 
        chat_id = await chat_service.ChatService.add_new_chat(new_chat=new_chat, session=session)
        await self.update_connected_users(first_user_id=first_user_id, second_user_id=second_user_id, session=session, chat_id=chat_id)
        await user_in_search_service.UserInSearchService.delete_user_in_search(user_id=second_user_id, session=session)
        await user_service.UserService.change_user_state(user_id=first_user_id, session=session, user_state=User_state.chatting_state)
        await user_service.UserService.change_user_state(user_id=second_user_id, session=session, user_state=User_state.chatting_state)
    
    async def update_connected_users(self, first_user_id:int, second_user_id:int, session:AsyncSession, chat_id:int):
        logging.info("Обновляем информацию о подключённых пользователях")
        await user_service.UserService.update_user_connected_user_and_chat_id(user_id=first_user_id, connected_user=second_user_id, chat_id=chat_id, session=session)
        await user_service.UserService.update_user_connected_user_and_chat_id(user_id=second_user_id, connected_user=first_user_id, chat_id=chat_id, session=session)