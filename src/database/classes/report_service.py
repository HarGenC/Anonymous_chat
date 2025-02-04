
from database.classes.user_service import UserService
from database.models import scenario, report, solved_report
from database.models import Reason_type, Punishment_type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, cast, Integer, exc
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from user_operation.schemas.databaseschemas import Report, SolvedReport
import logging

class ReportService:
    @staticmethod
    async def add_new_report(new_report:Report, session:AsyncSession):
        logging.info("Добавляем новую жалобу")
        try:
            stmt_add_new_punishment = insert(report).values(new_report.model_dump()).returning(report.c.id)
            report_id = await session.execute(stmt_add_new_punishment)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        report_id = report_id.all()
        if bool(report_id):
            return report_id[0][0]
    
    @staticmethod
    async def is_reported(user_id:int, session:AsyncSession) -> bool:
        logging.info("Проверяем был ли подана жалоба")
        user_row = await UserService.get_user_from_db(user_id=user_id, session=session)
        if not bool(user_row):
            return False
        try:
            stmt_check_user = select(report).where(report.c.user_id == user_id).where(report.c.chat_id == user_row[0][4])
            result = await session.execute(stmt_check_user)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        if bool(result):
            return bool(result.all())
    
    @staticmethod
    async def is_there_unsolved_report(report_id:int, session:AsyncSession):
        logging.info("Проверяем существует ли нерешённая жалоба")
        try:
            stmt_check_user = select(report).where(report.c.id == report_id)
            result = await session.execute(stmt_check_user)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        if not bool(result):
            return
        result = result.all()
        if bool(result):
            return result
    
    @staticmethod
    async def is_there_solved_report(report_id:int, session:AsyncSession):
        logging.info("Проверяем существует ли решённая жалоба")
        try:
            stmt_check_user = select(solved_report).where(solved_report.c.id == report_id)
            result = await session.execute(stmt_check_user)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        if not bool(result):
            return
        result = result.all()
        if bool(result):
            return result
    
    @staticmethod
    async def get_report(report_id:int, session:AsyncSession):
        logging.info("Пытаемся получить жалобу")
        report = await ReportService.is_there_unsolved_report(report_id=report_id, session=session)
        if bool(report):
            return report
        
        report = await ReportService.is_there_solved_report(report_id=report_id, session=session)
        if bool(report):
            return report
    
    @staticmethod
    async def add_solved_report(new_solved_report:SolvedReport, session:AsyncSession):
        logging.info("Добавляем решённую жалобу")
        solved_report_id = None
        try:
            stmt_add_new_solved_report = insert(solved_report).values(new_solved_report.model_dump()).returning(solved_report.c.id)
            solved_report_id = await session.execute(stmt_add_new_solved_report)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        if bool(solved_report_id):
            solved_report_id = solved_report_id.all()
            return solved_report_id[0][0]
    
    @staticmethod
    async def get_n_unsolved_reports(session:AsyncSession, n:int):
        logging.info("Получаем некоторое количество жалоб")
        unsolved_reports = None
        try:
            stmt_get_n_unsolved_reports = (
                select(report)
                .outerjoin(
                scenario,
                cast(report.c.id, Integer) == cast(scenario.c.scenario_state.op('->>')('report_id'), Integer)
            )
            .where(scenario.c.scenario_state.op('->>')('report_id').is_(None))
            )
            unsolved_reports = await session.execute(stmt_get_n_unsolved_reports)
        except exc.SQLAlchemyError as e:
            logging.error(e)

        n_unsolved_reports = unsolved_reports.fetchmany(size=n)
        if bool(n_unsolved_reports):
            return n_unsolved_reports
    
    @staticmethod
    async def delete_report(report_id:int, session:AsyncSession):
        logging.info("Удаляем жалобу")
        try:
            stmt_delete_report = delete(report).where(report.c.id == report_id)
            await session.execute(stmt_delete_report)
        except exc.SQLAlchemyError as e:
            logging.error(e)