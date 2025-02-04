import datetime
from database.classes import chat_service, user_service
from user_operation.models.states.current_state import *
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from database.database import get_async_session
from user_operation.models import user_state_machine as usm
from user_operation.models.states import menu_state
from telebot import apihelper
from database.models import User_state
from classes import user_history_table
from chatGPT import operations
from config import CHATGPT_USER_ID
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import telebot

class ChattingState(CurrentState):
    def __init__(self):
        super().__init__()
        self.register_commands()

    async def enter_state(self, user_manager:usm.UserStateManager):
        logging.info("Пользователь вошёл в состояние чаттинга")
        try:
            await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, text="Найден собеседник, приятного вам общения", reply_markup=self.create_user_started_chat_keyboard())
        except telebot.apihelper.ApiException as e:
            logging.error(e)

    async def update_state(self, user_manager:usm.UserStateManager):
        logging.info("Отправка пользователем сообщения")
        if user_manager.message.text in self.commands:
            await self.commands.get(user_manager.message.text)(user_manager)
        else:
            second_user_id = None
            chat_id = None
            async for session in get_async_session():
                second_user_id = await user_service.UserService.get_connected_user_id(first_user_id=user_manager.message.from_user.id, session=session)
                chat_id = await user_service.UserService.get_current_chat(user_manager.message.from_user.id, session=session)

            sender_user_history_manager = user_history_table.UserHistoryTableManager(user_manager.message.from_user.id)
            reciever_user_history_manager = user_history_table.UserHistoryTableManager(second_user_id)

            async for session in get_async_session():
                async with session.begin():
                    sender_user_state = await user_manager.current_state.is_state()
                    await sender_user_history_manager.add_message_in_history(state=sender_user_state,
                                                                             chat_id=chat_id,
                                                                             session=session,
                                                                             user_id=user_manager.message.from_user.id,
                                                                             file_id=user_manager.message.file_id,
                                                                             text=user_manager.message.text)
                    await reciever_user_history_manager.add_message_in_history(state=sender_user_state,
                                                                               chat_id=chat_id,
                                                                               session=session,
                                                                               user_id=user_manager.message.from_user.id,
                                                                               file_id=user_manager.message.file_id,
                                                                               text=user_manager.message.text)
            try:
                if not second_user_id == int(CHATGPT_USER_ID):
                    try:
                        await user_manager.bot.copy_message(chat_id=second_user_id,
                                                            from_chat_id=user_manager.message.from_user.id,
                                                            message_id=user_manager.message.id)
                    except telebot.apihelper.ApiException as e:
                        logging.error(e)
                else:
                    async for session in get_async_session():
                        async with session.begin():
                            message = await operations.send_and_get_chatGPT_message(user_id=user_manager.message.from_user.id, chat_id=chat_id, session=session, message=user_manager.message.text)

                            await sender_user_history_manager.add_message_in_history(state=sender_user_state,
                                                                             chat_id=chat_id,
                                                                             session=session,
                                                                             user_id=user_manager.message.from_user.id,
                                                                             text=message)
                            await reciever_user_history_manager.add_message_in_history(state=sender_user_state,
                                                                                    chat_id=chat_id,
                                                                                    session=session,
                                                                                    user_id=user_manager.message.from_user.id,
                                                                                    text=message)
                            if message == "Закончить диалог":
                                await self.chatgpt_finish_chat(user_manager=user_manager)
                            else:
                                try:
                                    await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id,
                                                                        text=message)
                                except telebot.apihelper.ApiException as e:
                                    logging.error(e)

            except apihelper.ApiTelegramException as e:
                if e.error_code == 403:
                    logging.info(f"User {user_manager.message.from_user.id} has blocked send this type of message.")
                    try:
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id,
                                                            text="Пользователь запретил принимать такой тип сообщений от бота")
                    except telebot.apihelper.ApiException as e:
                        logging.error(e)
                else:
                    logging.warning(f"Failed to send message to {user_manager.message.from_user.id}. Error: {e}")
                
    async def is_state(self):
        return User_state.chatting_state

    def register_commands(self):
        # Регистрация команд через вызов декоратора
        self.command("Закончить диалог")(self.finish_chat)
    
    def create_user_started_chat_keyboard(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Закончить диалог"))
        return markup
    
    async def disconnect(self, first_user_id:int, session:AsyncSession):
        logging.info("Разъединение двух пользователя в чате")
        second_user_id = await user_service.UserService.get_connected_user_id(first_user_id=first_user_id, session=session)
        await chat_service.ChatService.set_finish_time_for_user_chat(user_id=first_user_id, finished_at=datetime.datetime.utcnow(), session=session)
        if not first_user_id == int(CHATGPT_USER_ID):
            await user_service.UserService.update_field_connected_user(user_id=first_user_id, connected_user=-1, session=session)
            await user_service.UserService.change_user_state(user_id=first_user_id, session=session, user_state=User_state.menu_state)
        if not second_user_id == int(CHATGPT_USER_ID):
            await user_service.UserService.update_field_connected_user(user_id=second_user_id, connected_user=-1, session=session)
            await user_service.UserService.change_user_state(user_id=second_user_id, session=session, user_state=User_state.menu_state)
        return second_user_id

    async def finish_chat(self, user_manager:usm.UserStateManager):
        logging.info("Завершается диалог")
        second_user_is_admin = False
        async for session in get_async_session():
            async with session.begin():
                second_user_id = await self.disconnect(first_user_id=user_manager.message.from_user.id, session=session)
                if not second_user_id == int(CHATGPT_USER_ID):
                    second_user_is_admin = await user_service.UserService.is_user_admin(user_id=second_user_id, session=session)
                await user_manager.switch_state(current_state=menu_state.MenuState())
        try:
            if not second_user_id == int(CHATGPT_USER_ID):
                await user_manager.bot.send_message(chat_id=second_user_id, text="Собеседник закончил диалог", 
                                                    reply_markup=user_manager.current_state.create_starting_menu_keyboard(second_user_is_admin))
        except apihelper.ApiTelegramException as e:
            if e.error_code == 403:
                logging.info(f"User {user_manager.message.from_user.id} has blocked the bot.")
            else:
                logging.warning(f"Failed to send message to {user_manager.message.from_user.id}. Error: {e}")

    async def chatgpt_finish_chat(self, user_manager:usm.UserStateManager):
        logging.info("ЧатГПТ завершает чат")
        async for session in get_async_session():
            async with session.begin():
                await self.disconnect(first_user_id=user_manager.message.from_user.id, session=session)
                user_is_admin = await user_service.UserService.is_user_admin(user_id=user_manager.message.from_user.id, session=session)
                user_manager.current_state = menu_state.MenuState()
                try:
                    await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, text="Собеседник закончил диалог", 
                                                        reply_markup=user_manager.current_state.create_starting_menu_keyboard(user_is_admin))
                except telebot.apihelper.ApiException as e:
                    logging.error(e)