import pytest
import datetime
from sqlalchemy import select
from classes import chatgpt_person
from database.models import chatgpt_chat
from src.database.classes import chatgpt_chat_service
from user_operation.schemas.databaseschemas import ChatGPTPerson


@pytest.mark.parametrize("user_id, chat_id, expectation", [
    (103, 3, [(103, 3,)]),  # test case 1
    (101, 101, None)  # test case 2
])
@pytest.mark.asyncio(loop_scope="session")
async def test_add_chatgpt_person(user_id:int, chat_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = None
    time = datetime.datetime(2024, 1, 1, 0, 0, 0, 0)
    new_chatgpt_person = chatgpt_person.ChatGPTPerson()
    gpt_person = ChatGPTPerson(
        user_id=user_id,
        chat_id=chat_id,
        chatgpt_person=new_chatgpt_person.text
    )
    chatgpt_person_id = await chatgpt_chat_service.ChatgptChatService.add_chatgpt_person(gpt_person, session)
    if bool(chatgpt_person_id):
        expectation[0] = (chatgpt_person_id,) + expectation[0] + (new_chatgpt_person.text,)
        await savepoint.commit()       
        query = select(chatgpt_chat).where(chatgpt_chat.c.id == chatgpt_person_id)
        result = await session.execute(query)
        result = result.all()
    print(result)
    assert result == expectation

@pytest.mark.parametrize("user_id, chat_id, expectation", [
    (102, 4, 'Ты – человек, который общается в анонимном чате. Используй непринужденный и разговорный стиль.'),  # test case 1
    (101, 101, None)  # test case 2
])
@pytest.mark.asyncio(loop_scope="session")
async def test_get_chatgpt_person(user_id:int, chat_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = await chatgpt_chat_service.ChatgptChatService.get_chatgpt_person(user_id, chat_id, session)
    assert result == expectation