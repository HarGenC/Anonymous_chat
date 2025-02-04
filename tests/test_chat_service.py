import pytest
import datetime
from sqlalchemy import select
from database.models import chat, user
from src.database.classes import chat_service
from user_operation.schemas.databaseschemas import Chat


@pytest.mark.parametrize("first_user_id, second_user_id, expectation", [
    (100, 101, [(100, 101, datetime.datetime(2024, 1, 1, 0, 0), None)]),  # test case 1
    (1, 2, None)  # test case 2
])
@pytest.mark.asyncio(loop_scope="session")
async def test_add_new_chat(first_user_id:int, second_user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = None
    time = datetime.datetime(2024, 1, 1, 0, 0, 0, 0)
    new_chat = Chat(
        first_user_id = first_user_id,
        second_user_id = second_user_id,
        started_at = time
    )
    chat_id = await chat_service.ChatService.add_new_chat(new_chat, session)
    if bool(chat_id):
        expectation[0] = (chat_id,) + expectation[0]
        await savepoint.commit()       
        query = select(chat).where(chat.c.id == chat_id)
        result = await session.execute(query)
        result = result.all()
    assert result == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (104, [(1, 104, 105, datetime.datetime(2024, 1, 1, 0, 0), datetime.datetime(2024, 1, 1, 1, 0))]),  # test case 1
    (1, [])  # test case 2
])
@pytest.mark.asyncio(loop_scope="session")
async def test_set_finish_time_for_user_chat(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    time = datetime.datetime(2024, 1, 1, 1, 0, 0, 0)
    await chat_service.ChatService.set_finish_time_for_user_chat(user_id, time, session)
    await savepoint.commit()

    query = select(chat).where(chat.c.id == select(user.c.prev_chat_id) \
                   .where(user.c.id == user_id).scalar_subquery())
    result = await session.execute(query)
    result = result.all()
    assert result == expectation

@pytest.mark.parametrize("report_id, expectation", [
    (100, None),  # test case 1 invalid report id
    (1, 100)  # test case 2 valid report id
])
@pytest.mark.asyncio(loop_scope="session")
async def test_get_reported_user(report_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    reported_user_id = await chat_service.ChatService.get_reported_user(report_id, session)

    assert reported_user_id == expectation