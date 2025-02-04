import pytest
import datetime
from sqlalchemy import select
from database.models import report, solved_report
from src.database.classes import operation_state_service
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
    report_id = await operation_state_service.OperationStateService.check_and_update_admin_panel_state()
    if bool(report_id):
        expectation[0] = (report_id,) + expectation[0]
        await savepoint.commit()       
        query = select(report).where(report.c.id == report_id)
        result = await session.execute(query)
        result = result.all()
    assert result == expectation