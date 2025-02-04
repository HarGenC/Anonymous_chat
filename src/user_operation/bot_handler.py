from config import API_CHATBOT_KEY
from user_operation.schemas.databaseschemas import User
from database.models import Role_type, User_state
from database.classes.chat_service import ChatService
from database.classes.operation_state_service import OperationStateService
from database.classes.punishment_service import PunishmentService
from database.classes.user_service import UserService
from database.database import get_async_session, add_new_user_history_table
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from user_operation.models.user_state_machine import *
from telebot.types import BotCommand
from user_operation.models.states import menu_state
from user_operation.models.states import chatting_state
from classes import user_history_table
import datetime
import logging
import telebot

bot = AsyncTeleBot(API_CHATBOT_KEY)

@bot.message_handler(commands=['start'])
async def handle_start(message: types.Message) -> None:
    logging.info("Запуск команды старт")
    commands = [
    BotCommand("start", "Запустить бота"),
    BotCommand("reset", "Перезапустить бота"),
    ]

    await bot.set_my_commands(commands)

    if message.chat.type in ["group", "supergroup"]:
        await bot.leave_chat(message.chat.id)
    async for session in get_async_session():
        async with session.begin():
            new_user = None
            try:
                new_user = User(
                    id = message.from_user.id,
                    registered_at = datetime.datetime.utcnow(),
                    role_id = Role_type.user,
                    connected_user = -1,
                    prev_chat_id = -1,
                    state = User_state.menu_state,
                    username = message.from_user.username
                )
            except Exception as e:
                logging.error(e) 
            result = await UserService.add_new_user(new_user=new_user, session=session)
    async for session in get_async_session():
        async with session.begin():
            await add_new_user_history_table(message.from_user.id)

    if result["status"] == "success":
        print("register new user")
        logging.debug("Присылаю сообщение пользователю")
        user = await OperationStateService.get_user_state_manager(user_id = message.from_user.id, bot=bot, mymessage=msg.Message(text=message.text, id=message.from_user.id, msg_id=message.id))
        async for session in get_async_session():
            async with session.begin():
                user_history_manager = user_history_table.UserHistoryTableManager(message.from_user.id)
                await user_history_manager.add_message_in_history(state=await user.current_state.is_state(),
                                                                  chat_id=await UserService.get_current_chat(message.from_user.id, session=session),
                                                                  user_id=user.message.from_user.id,
                                                                  session=session,
                                                                  file_id="None",
                                                                  text="/start")
        await user.switch_state(menu_state.MenuState())

@bot.message_handler(commands=['reset'])
async def handle_reset(message: types.Message) -> None:
    logging.info("Запуск команды сброса состояния пользователя")

    if message.chat.type in ["group", "supergroup"]:
        await bot.leave_chat(message.chat.id)
    async for session in get_async_session():
        if await PunishmentService.is_user_punished(user_id=message.from_user.id, session=session):
            return
    user = await OperationStateService.get_user_state_manager(user_id = message.from_user.id,
                                                              bot=bot,
                                                              mymessage=msg.Message(text=message.text,
                                                                                    id=message.from_user.id,
                                                                                    msg_id=message.id))

    async for session in get_async_session():
        async with session.begin():
            user_history_manager = user_history_table.UserHistoryTableManager(message.from_user.id)
            await user_history_manager.add_message_in_history(state=await user.current_state.is_state(),
                                                              chat_id=await UserService.get_current_chat(message.from_user.id, session=session),
                                                              session=session,
                                                              user_id=user.message.from_user.id,
                                                              file_id="None",
                                                              text="/reset")

    if not await OperationStateService.quit_from_all_state_in_menu(user_state_manager=user,
                                                       bot_answer="Ваш собеседник перезапустил себе бота"):
        await user.switch_state(menu_state.MenuState())

@bot.message_handler(commands=['reset_table'])
async def handle_reset_table(message:types.Message):
    await add_new_user_history_table(message.from_user.id)


@bot.message_handler(content_types=['text'])
async def func(message: types.Message):
    logging.info("Обработка текстового сообщения")
    try:
        if message.chat.type in ["group", "supergroup"]:
            await bot.leave_chat(message.chat.id)
            return
    except telebot.apihelper.ApiException as e:
        logging.error(e)
        
    async for session in get_async_session():
        if await PunishmentService.is_user_punished(user_id=message.from_user.id, session=session):
            return
    user = await OperationStateService.get_user_state_manager(user_id = message.from_user.id, bot=bot, mymessage=msg.Message(text=message.text, id=message.from_user.id, msg_id=message.id))
    if not isinstance(user.current_state, chatting_state.ChattingState):
        async for session in get_async_session():
            async with session.begin():
                user_history_manager = user_history_table.UserHistoryTableManager(message.from_user.id)
                await user_history_manager.add_message_in_history(state=await user.current_state.is_state(),
                                                                  chat_id=await UserService.get_current_chat(message.from_user.id, session=session),
                                                                  session=session,
                                                                  user_id=user.message.from_user.id,
                                                                  file_id="None",
                                                                  text=message.text)
    await user.update()

@bot.message_handler(content_types=['audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice'])
async def chatting(message: types.Message):
    logging.info("Обработка не текстового типа сообщения")
    try:
        if message.chat.type in ["group", "supergroup"]:
            await bot.leave_chat(message.chat.id)
            return
    except telebot.apihelper.ApiException as e:
        logging.error(e)

    async for session in get_async_session():
        if await PunishmentService.is_user_punished(user_id=message.from_user.id, session=session):
            return
    user = await OperationStateService.get_user_state_manager(user_id = message.from_user.id, bot=bot, mymessage=msg.Message(text=message.text, id=message.from_user.id, msg_id=message.id))
    file_id = None

    # Проверка типа контента и извлечение file_id
    if message.content_type == 'document':
        file_id = message.document.file_id
    elif message.content_type == 'photo':
        file_id = message.photo[-1].file_id
    elif message.content_type == 'video':
        file_id = message.video.file_id
    elif message.content_type == 'audio':
        file_id = message.audio.file_id
    elif message.content_type == 'sticker':
        file_id = message.sticker.file_id
    elif message.content_type == 'voice':
        file_id = message.voice.file_id
    elif message.content_type == 'video_note':
        file_id = message.video_note.file_id
    user.message.file_id = str(file_id)
    user.message.text = message.caption
    if isinstance(user.current_state, chatting_state.ChattingState):
        await user.update()
    pass