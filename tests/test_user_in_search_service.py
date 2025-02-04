import pytest
import datetime
from sqlalchemy import select
from database.models import user_in_search
from src.database.classes import user_in_search_service
from user_operation.schemas.databaseschemas import UserInSearch
from database.models import User_filter


@pytest.mark.parametrize("user_id, filter, expectation", [
    (101, User_filter.all, [(101, datetime.datetime(2024, 1, 1, 0, 0), User_filter.all)]),  # test case 1
    (1, User_filter.all, None)
])
@pytest.mark.asyncio(loop_scope="session")
async def test_add_user_in_search(user_id:int, filter:User_filter, expectation, db_session:tuple):
    session, savepoint = db_session
    result = None
    time = datetime.datetime(2024, 1, 1, 0, 0, 0, 0)
    new_user_in_search = UserInSearch(
        user_id = user_id,
        started_at = time,
        filter = filter
    )

    user_in_search_id = await user_in_search_service.UserInSearchService.add_user_in_search(new_user_in_search, session)
    if bool(user_in_search_id):
        expectation[0] = (user_in_search_id,) + expectation[0]
        await savepoint.commit()
        query = select(user_in_search).where(user_in_search.c.id == user_in_search_id)
        result = await session.execute(query)
        result = result.all()
    assert result == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (105, None),  # test case 1
    (1, None)
])
@pytest.mark.asyncio(loop_scope="session")
async def test_delete_user_in_search(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = None
    user_in_search_id = await user_in_search_service.UserInSearchService.delete_user_in_search(user_id, session)
    if bool(user_in_search_id):
        expectation[0] = (user_in_search_id,) + expectation[0]
        await savepoint.commit()
        query = select(user_in_search).where(user_in_search.c.id == user_in_search_id)
        result = await session.execute(query)
        result = result.all()
    assert result == expectation

@pytest.mark.parametrize("filter, expectation", [
    (User_filter.all, 105)
])
@pytest.mark.asyncio(loop_scope="session")
async def test_find_first_user_in_search(filter:User_filter, expectation, db_session:tuple):
    session, savepoint = db_session

    result = await user_in_search_service.UserInSearchService.find_first_user_in_search(session, filter)
    assert result == expectation

@pytest.mark.parametrize("expectation", [
    ((1, 105, datetime.datetime(2024, 1, 1, 0, 0), User_filter.all))
])
@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_in_search_with_the_longest_time(expectation, db_session:tuple):
    session, savepoint = db_session

    result = await user_in_search_service.UserInSearchService.get_user_in_search_with_the_longest_time(session)
    assert result == expectation