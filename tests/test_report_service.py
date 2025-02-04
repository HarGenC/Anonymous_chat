import pytest
import datetime
from sqlalchemy import select
from database.models import report, solved_report
from src.database.classes import report_service
from user_operation.schemas.databaseschemas import Report, SolvedReport
from database.models import Reason_type, Punishment_type


@pytest.mark.parametrize("chat_id, reason, user_id, user_commentary, expectation", [
    (1, Reason_type.insult, 101, "insult", [(1, Reason_type.insult, 101, 'insult', datetime.datetime(2024, 1, 1, 0, 0))]),  # test case 1
])
@pytest.mark.asyncio(loop_scope="session")
async def test_add_new_report(chat_id:int, reason:Reason_type, user_id:int, user_commentary:str, expectation, db_session:tuple):
    session, savepoint = db_session
    result = None
    time = datetime.datetime(2024, 1, 1, 0, 0, 0, 0)
    new_report = Report(
                            chat_id = chat_id,
                            reason = reason,
                            user_id = user_id,
                            user_commentary = user_commentary,
                            created_at = time
                        )
    report_id = await report_service.ReportService.add_new_report(new_report, session)
    if bool(report_id):
        expectation[0] = (report_id,) + expectation[0]
        await savepoint.commit()       
        query = select(report).where(report.c.id == report_id)
        result = await session.execute(query)
        result = result.all()
    assert result == expectation

@pytest.mark.parametrize("id, chat_id, reason, user_id, user_commentary, admin_id_solved_report, admin_commentary, type_of_punishment, expectation", [
    (100, 1, Reason_type.insult, 101, "insult", 101, "insult", Punishment_type.ban, [( 1, Reason_type.insult, 101, 'insult', datetime.datetime(2024, 1, 1, 0, 0), datetime.datetime(2024, 1, 1, 0, 0), 101, Punishment_type.ban, 'insult')]),  # test case 1
    (57, 2, Reason_type.insult, 101, "insult", 101, "insult", Punishment_type.ban, [( 2, Reason_type.insult, 101, 'insult', datetime.datetime(2024, 1, 1, 0, 0), datetime.datetime(2024, 1, 1, 0, 0), 101, Punishment_type.ban, 'insult')]),  # test case 1
])
@pytest.mark.asyncio(loop_scope="session") #ИСПРАВИТЬ (ПЕРЕДЕЛАТЬ ФУНКЦИЮ, чтобы нужно было id назначать) 
async def test_add_solved_report(id:int, chat_id:int, reason:Reason_type, user_id:int, user_commentary:str, admin_id_solved_report:int, admin_commentary:str, type_of_punishment:Punishment_type, expectation, db_session:tuple):
    session, savepoint = db_session
    result = None
    time = datetime.datetime(2024, 1, 1, 0, 0, 0, 0)
    new_solved_report = SolvedReport(
        id = id,
        chat_id = chat_id,
        reason = reason,
        user_id = user_id,
        user_commentary = user_commentary,
        created_at = time,
        solved_at = time,
        admin_id_solved_report=admin_id_solved_report,
        type_of_punishment = type_of_punishment,
        admin_commentary = admin_commentary
    )
    solved_report_id = await report_service.ReportService.add_solved_report(new_solved_report, session)
    if bool(solved_report_id):
        expectation[0] = (solved_report_id,) + expectation[0]
        await savepoint.commit()       
        query = select(solved_report).where(solved_report.c.id == solved_report_id)
        result = await session.execute(query)
        result = result.all()
    assert result == expectation

@pytest.mark.parametrize("report_id, expectation", [
    (1, None),  # test case 1 valid report id
    (101, None),  # test case 2 invalid report id
])
@pytest.mark.asyncio(loop_scope="session")
async def test_delete_report(report_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = None
    report_id = await report_service.ReportService.delete_report(report, session)
    if bool(report_id):
        expectation[0] = (report_id,) + expectation[0]
        await savepoint.commit()       
        query = select(report).where(report.c.id == report_id)
        result = await session.execute(query)
        result = result.all()
    assert result == expectation

@pytest.mark.parametrize("n, expectation", [
    (0, None),  # test case 1 valid report id
    (1, [(5, 4, Reason_type.insult, 102, 'Оскорбление', datetime.datetime(2024, 1, 1, 0, 0))]),  # test case 2 valid report id

    (2, [(5, 4, Reason_type.insult, 102, 'Оскорбление', datetime.datetime(2024, 1, 1, 0, 0)),
         (4, 3, Reason_type.insult, 103, 'Оскорбление', datetime.datetime(2024, 1, 1, 0, 0))]),  # test case 3

    (101, [(5, 4, Reason_type.insult, 102, 'Оскорбление', datetime.datetime(2024, 1, 1, 0, 0)),
        (4, 3, Reason_type.insult, 103, 'Оскорбление', datetime.datetime(2024, 1, 1, 0, 0)),
        (3, 1, Reason_type.insult, 105, 'Оскорбление', datetime.datetime(2024, 1, 1, 0, 0))]),  # test case 4
])
@pytest.mark.asyncio(loop_scope="session")
async def test_get_n_unsolved_reports(n:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = await report_service.ReportService.get_n_unsolved_reports(session, n)
    assert result == expectation

@pytest.mark.parametrize("report_id, expectation", [
    (1, [(1, 2, Reason_type.insult, 101, 'Оскорбление', datetime.datetime(2024, 1, 1, 0, 0))]),  # test case 1 valid report id
    (2, [(2, 1, Reason_type.insult, 104, 'insult', datetime.datetime(2024, 1, 1, 0, 0), datetime.datetime(2024, 1, 1, 0, 0), 109, Punishment_type.ban, 'insult')]),  # test case 2 Solved_report ИСПРАВИТЬ ДАННЫЙ ТЕСТ

    (100, None),  # test case 3
])
@pytest.mark.asyncio(loop_scope="session")
async def test_get_report(report_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = await report_service.ReportService.get_report(report_id, session)
    assert result == expectation

@pytest.mark.parametrize("user_id, expectation", [
    (104, False),  # test case 1 valid report id
    (105, True),  # test case 2 
    (1, False),  # test case 3 
])
@pytest.mark.asyncio(loop_scope="session")
async def test_is_reported(user_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = await report_service.ReportService.is_reported(user_id, session)
    assert result == expectation

@pytest.mark.parametrize("report_id, expectation", [
    (1, [(1, 2, Reason_type.insult, 101, 'Оскорбление', datetime.datetime(2024, 1, 1, 0, 0))]),  # test case 1 valid report id
    (100, None),  # test case 2 
])
@pytest.mark.asyncio(loop_scope="session")
async def test_is_there_unsolved_report(report_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = await report_service.ReportService.is_there_unsolved_report(report_id, session)
    assert result == expectation

@pytest.mark.parametrize("report_id, expectation", [
    (2, [(2, 1, Reason_type.insult, 104, 'insult', datetime.datetime(2024, 1, 1, 0, 0), datetime.datetime(2024, 1, 1, 0, 
0), 109, Punishment_type.ban, 'insult')]),  # test case 1 ИСПРАВИТЬ
    (100, None),  # test case 2
])
@pytest.mark.asyncio(loop_scope="session")
async def test_is_there_solved_report(report_id:int, expectation, db_session:tuple):
    session, savepoint = db_session
    result = await report_service.ReportService.is_there_solved_report(report_id, session)
    assert result == expectation