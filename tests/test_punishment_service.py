import pytest
import datetime
from sqlalchemy import select
from database.models import punishment
from src.database.classes import punishment_service
from user_operation.schemas.databaseschemas import Punishment
from database.models import Reason_type, Punishment_type


@pytest.mark.parametrize("reason, user_id, expectation", [
    (Reason_type.insult, 101, [(101, Reason_type.insult, datetime.datetime(2024, 1, 1, 0, 0), Punishment_type.ban, datetime.datetime(2124, 1, 1, 0, 0))]),  # test case 1
    (Reason_type.insult, 1, None)
])
@pytest.mark.asyncio(loop_scope="session")
async def test_apply_punishment(reason:Reason_type, user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = None
    time = datetime.datetime(2024, 1, 1, 0, 0, 0, 0)
    new_punishment = Punishment(
                    user_id = user_id,
                    reason = reason,
                    created_at = time,
                    type_of_punishment = Punishment_type.ban,
                    ended_at = time.replace(year=time.year + 100)
                )
    punishment_id = await punishment_service.PunishmentService.apply_punishment(session, new_punishment)
    if bool(punishment_id):
        expectation[0] = (punishment_id,) + expectation[0]
        await savepoint.commit()       
        query = select(punishment).where(punishment.c.id == punishment_id)
        result = await session.execute(query)
        result = result.all()
    assert result == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (106, None),  # test case 1
    (1, None)
])
@pytest.mark.asyncio(loop_scope="session")
async def test_delete_punishment_with_user_id(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session

    await punishment_service.PunishmentService.delete_punishment_with_user_id(user_id, session)
    await savepoint.commit()

    query = select(punishment).where(punishment.c.user_id == user_id)
    result = await session.execute(query)
    result = result.all()
    if not bool(result):
        result = None

    assert result == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (106, True),  # test case 1
    (102, False),
    (1, False)
])
@pytest.mark.asyncio(loop_scope="session")
async def test_is_user_punished(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = await punishment_service.PunishmentService.is_user_punished(user_id, session)

    assert result == expectation