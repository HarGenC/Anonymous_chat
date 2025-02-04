import pytest
import datetime
import json
from sqlalchemy import select
from database.models import scenario
from src.database.classes import scenario_service
from user_operation.schemas.databaseschemas import Scenario
from sqlalchemy.exc import IntegrityError


@pytest.mark.parametrize("user_id, scenario_state, expectation", [
    (101, {"status":"Nothing"}, [(101, datetime.datetime(2024, 1, 1, 0, 0), {'status': 'Nothing'})]),  # test case 1
    (1, {"status":"Nothing"}, None),  # test case 2 вызывается ошибка
])
@pytest.mark.asyncio(loop_scope="session")
async def test_add_user_status_scenario(user_id:int, scenario_state:json, expectation, db_session:tuple):
    session, savepoint = db_session
    result = None
    time = datetime.datetime(2024, 1, 1, 0, 0, 0, 0)
    new_scenario = Scenario(
        user_id = user_id,
        started_at = time,
        scenario_state = scenario_state
    )
    scenario_id = await scenario_service.ScenarioService.add_user_status_scenario(new_scenario, session)

    if bool(scenario_id):
        expectation[0] = (scenario_id,) + expectation[0]
        await savepoint.commit()       
        query = select(scenario).where(scenario.c.id == scenario_id)
        result = await session.execute(query)
        result = result.all()

    assert result == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (107, None),  # test case 1
    (1, None),  # test case 2 вызывается ошибка
])
@pytest.mark.asyncio(loop_scope="session")
async def test_delete_user_status_scenario(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    time = datetime.datetime(2024, 1, 1, 0, 0, 0, 0)
    await scenario_service.ScenarioService.delete_user_status_scenario(user_id, session)

    await savepoint.commit()       
    query = select(scenario).where(scenario.c.user_id == user_id)
    result = await session.execute(query)
    if bool(result):
        result = result.all()
    if not bool(result):
        result = None

    assert result == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (107, {'report_id': 1}),  # test case 1
    (1, None),  # test case 2 вызывается ошибка
])
@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_status_scenario(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = await scenario_service.ScenarioService.get_user_status_scenario(user_id, session)

    assert result == expectation

@pytest.mark.parametrize("report_id, expectation", [
    (107, False),  # test case 1
    (1, True),  # test case 2 вызывается ошибка
    (2, False),  # test case 2 вызывается ошибка
])
@pytest.mark.asyncio(loop_scope="session")
async def test_is_report_occupied(report_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = await scenario_service.ScenarioService.is_report_occupied(report_id, session)

    assert result == expectation