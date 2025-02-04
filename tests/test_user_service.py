import pytest
import datetime
from sqlalchemy import select
from database.models import user
from src.database.classes import user_service
from database.models import Role_type, User_state
from user_operation.schemas.databaseschemas import User


@pytest.mark.parametrize("user_id, username, status, expectation", [
    (1, 'test1', {'status': 'success'}, [(1, datetime.datetime(2024, 1, 1, 0, 0, 0, 0), Role_type.user, -1, -1, User_state.menu_state, 'test1')]),  # test case 1
    (101, 'test666', {'status': 'failure'}, [(101, datetime.datetime(2024, 1, 1, 0, 0, 0, 0), Role_type.admin, -1, -1, User_state.menu_state, 'test101')])  # test case 2
])
@pytest.mark.asyncio(loop_scope="session")
async def test_add_new_user(user_id:int, username:str, status, expectation, db_session:tuple):
    session, savepoint = db_session
    time = datetime.datetime(2024, 1, 1, 0, 0, 0, 0)
    new_user = User(
        id = user_id,
        registered_at = time,
        role_id = Role_type.user,
        connected_user = -1,
        prev_chat_id = -1,
        state = User_state.menu_state,
        username = username
    )
    assert await user_service.UserService.add_new_user(new_user=new_user, session=session) == status
    
    await savepoint.commit()       
    query = select(user).where(user.c.id == user_id)
    result = await session.execute(query)
    result = result.all()
    assert result == expectation

@pytest.mark.parametrize("user_id, type_of_role, expectation", [
    (101, Role_type.admin, [(Role_type.admin,)]), # test case 1 admin -> admin
    (1, Role_type.admin, []), # test case 2 invalid id -> admin
    (103, Role_type.admin, [(Role_type.admin,)])  # test case 3 user -> admin
])
@pytest.mark.asyncio(loop_scope="session")
async def test_change_role(user_id:int, type_of_role:Role_type, expectation, db_session:tuple):
    session, savepoint = db_session
    
    await user_service.UserService.change_user_role(user_id=user_id, type_of_role=type_of_role, session=session)
    await savepoint.commit()

    query = select(user.c.role_id).where(user.c.id == user_id)
    result = await session.execute(query)
    result = result.all()
    assert result == expectation

@pytest.mark.parametrize("user_id, user_state, expectation", [
    (103, User_state.menu_state, [(User_state.menu_state,)]), # test case 1 menu -> menu
    (1, User_state.menu_state, []), # test case 2 invalid id -> menu
    (101, User_state.admin_panel_state, [(User_state.admin_panel_state,)])  # test case 3 menu -> admin panel
])
@pytest.mark.asyncio(loop_scope="session")
async def test_change_state(user_id:int, user_state:User_state, expectation, db_session:tuple):
    session, savepoint = db_session
    
    await user_service.UserService.change_user_state(user_id=user_id, user_state=user_state, session=session)
    await savepoint.commit()

    query = select(user.c.state).where(user.c.id == user_id)
    result = await session.execute(query)
    result = result.all()
    assert result == expectation
        
@pytest.mark.parametrize("user_id, expectation", [
    (100, -1), # test case 1 valid id -> -1
    (1, None), # test case 2 invalid id -> None
])
@pytest.mark.asyncio(loop_scope="session")
async def test_get_connected_user_id(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    assert await user_service.UserService.get_connected_user_id(first_user_id=user_id, session=session) == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (100, -1), # test case 1 valid id -> -1
    (1, None), # test case 2 invalid id -> None
])
@pytest.mark.asyncio(loop_scope="session")
async def test_get_current_chat(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    assert await user_service.UserService.get_current_chat(user_id=user_id, session=session) == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (101, [(101, datetime.datetime(2024, 1, 1, 0, 0), Role_type.admin, -1, -1, User_state.menu_state, 'test101')]), # test case 1
    (1, None), # test case 2 invalid id -> None
])
@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_from_db(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    assert await user_service.UserService.get_user_from_db(user_id=user_id, session=session) == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (100, User_state.admin_panel_state), # test case 1 valid id -> -1
    (1, None), # test case 2 invalid id -> None
])
@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_state(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    assert await user_service.UserService.get_user_state(user_id=user_id, session=session) == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (100, 'test100'), # test case 1 valid id -> -1
    (1, None), # test case 2 invalid id -> None
])
@pytest.mark.asyncio(loop_scope="session")
async def test_get_username_with_user_id(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    assert await user_service.UserService.get_username_with_user_id(user_id=user_id, session=session) == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (100, True), # test case 1 valid id -> -1
    (1, False), # test case 2 invalid id -> None
])
@pytest.mark.asyncio(loop_scope="session")
async def test_is_there_user(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    assert await user_service.UserService.is_there_user(user_id=user_id, session=session) == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (100, False), # test case 1 valid id -> False
    (101, True), # test case 2 valid id -> True
    (1, False), # test case 3 invalid id -> False
])
@pytest.mark.asyncio(loop_scope="session")
async def test_is_user_admin(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    assert await user_service.UserService.is_user_admin(user_id=user_id, session=session) == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (100, False), # test case 1 valid id -> False
    (104, True), # test case 2 valid id -> True
    (1, False), # test case 3 invalid id -> False
])
@pytest.mark.asyncio(loop_scope="session")
async def test_is_user_connected(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    assert await user_service.UserService.is_user_connected(user_id=user_id, session=session) == expectation

@pytest.mark.parametrize("user_id, connected_user, expectation", [
    (100, 101, [(100, datetime.datetime(2024, 1, 1, 0, 0), Role_type.user, 101, -1, User_state.admin_panel_state, 'test100')]), # test case 1 valid id -> -1
    (1, 100, []), # test case 2 invalid id -> None
])
@pytest.mark.asyncio(loop_scope="session")
async def test_update_field_connected_user(user_id:int, connected_user:int, expectation, db_session:tuple):
    session, savepoint = db_session
    await user_service.UserService.update_field_connected_user(user_id=user_id, connected_user=connected_user, session=session)
    await savepoint.commit()

    query = select(user).where(user.c.id == user_id)
    result = await session.execute(query)
    result = result.all()
    assert result == expectation

@pytest.mark.parametrize("user_id, connected_user, chat_id, expectation", [
    (100, 101, 2, [(100, datetime.datetime(2024, 1, 1, 0, 0), Role_type.user, 101, 2, User_state.admin_panel_state, 'test100')]), # test case 1 valid id -> -1
    (1, 100, 2, []), # test case 2 invalid id -> None
])
@pytest.mark.asyncio(loop_scope="session")
async def test_update_user_connected_user_and_chat_id(user_id:int, connected_user:int, chat_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    await user_service.UserService.update_user_connected_user_and_chat_id(user_id=user_id, connected_user=connected_user, chat_id=chat_id, session=session)
    await savepoint.commit()

    query = select(user).where(user.c.id == user_id)
    result = await session.execute(query)
    result = result.all()
    assert result == expectation