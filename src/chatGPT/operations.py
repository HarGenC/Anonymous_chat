import logging
import openai
from openai import OpenAIError
from sqlalchemy.ext.asyncio import AsyncSession
from telebot.async_telebot import AsyncTeleBot
from config import API_CHATGPT_KEY, CHATGPT_USER_ID
from classes import output_manager, chatgpt_person, user_history_table
from classes import message as msg
from database.classes import chatgpt_chat_service, user_in_search_service, user_service, chat_service, operation_state_service
from database.models import User_state
from user_operation.models.states import chatting_state
from user_operation.schemas.databaseschemas import ChatGPTPerson

client = openai.AsyncOpenAI(api_key=API_CHATGPT_KEY)

async def send_and_get_chatGPT_message(user_id:int, chat_id:int, session:AsyncSession, message:str):
    logging.info("Отправляем запрос чатуГПТ и получаем ответ")
    user_history_manager = user_history_table.UserHistoryTableManager(user_id=user_id)

    history = await user_history_manager.get_user_history_in_chat(chat_id=chat_id, session=session)

    chatgpt_person = await chatgpt_chat_service.ChatgptChatService.get_chatgpt_person(user_id=user_id, chat_id=chat_id, session=session)
    messages = [{'role': 'system', 'content': chatgpt_person}]

    output_text_manager = output_manager.OutputManager(history)
    messages.extend(await output_text_manager.do_for_chatgpt_output(CHATGPT_USER_ID))

    messages.append({'role': 'user', 'content': message})

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.9,
            top_p=0.9,
            presence_penalty=0.6,
            frequency_penalty=0.4
        )
        return response.choices[0].message.content
    except OpenAIError as e:
        logging.error(e)

async def connect_with_chatGPT(user_id:int, bot:AsyncTeleBot, session:AsyncSession):
    logging.info("Соединяем пользователя с чатомГПТ")
    chat_id = await chat_service.ChatService.add_new_chat(first_user_id=user_id, second_user_id=int(CHATGPT_USER_ID), session=session)
    await user_service.UserService.update_user_connected_user_and_chat_id(user_id=user_id, connected_user=int(CHATGPT_USER_ID), chat_id=chat_id, session=session)
    
    new_chatgpt_person = chatgpt_person.ChatGPTPerson()
    gpt_person = None
    try:
        gpt_person = ChatGPTPerson(
            user_id=user_id,
            chat_id=chat_id,
            chatgpt_person=new_chatgpt_person.text
        )
    except Exception as e:
        logging.error(e)
        
    await chatgpt_chat_service.ChatgptChatService.add_chatgpt_person(chatgpt_person=gpt_person, session=session)
    user_state_manager = await operation_state_service.OperationStateService.get_user_state_manager(user_id=user_id, bot=bot, mymessage=msg.Message(text="Nothing", id=user_id, msg_id=-1))
    await user_in_search_service.UserInSearchService.delete_user_in_search(user_id=user_id, session=session)
    await user_service.UserService.change_user_state(user_id=user_id, session=session, user_state=User_state.chatting_state)
    await user_state_manager.switch_state(current_state=chatting_state.ChattingState())