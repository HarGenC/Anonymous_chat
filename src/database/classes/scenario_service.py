
from database.models import scenario
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, JSON, cast, Integer, exc
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
import json
from user_operation.schemas.databaseschemas import Scenario
import logging

class ScenarioService:

    @staticmethod
    async def add_user_status_scenario(new_scenario:Scenario, session:AsyncSession):
        logging.info("Добавляем сценарий пользователю")
        result = None
        try:
            stmt_add_user_status_scenario = insert(scenario).values(new_scenario.model_dump()).returning(scenario.c.id)
            result = await session.execute(stmt_add_user_status_scenario)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        if not bool(result):
            return
        result = result.all()
        if bool(result):
            return result[0][0]

    @staticmethod
    async def get_user_status_scenario(user_id:int, session:AsyncSession):
        logging.info("Получаем сценарий пользователя")
        result = None
        try:
            stmt_select_user_status_scenario = select(scenario.c.scenario_state).where(scenario.c.user_id == user_id)
            result = await session.execute(stmt_select_user_status_scenario)
        except exc.SQLAlchemyError as e:
            logging.error(e)

        result_json = result.all()
        if bool(result_json):
            return result_json[0][0]

    @staticmethod
    async def delete_user_status_scenario(user_id:int, session:AsyncSession):
        logging.info("Удаляем сценарий пользователя")
        try:
            stmt_delete_user_status_scenario = delete(scenario).where(scenario.c.user_id == user_id)
            await session.execute(stmt_delete_user_status_scenario)
        except exc.SQLAlchemyError as e:
            logging.error(e)

    @staticmethod
    async def update_user_status_scenario(user_id:int, json_sctructure:json, session:AsyncSession):
        logging.info("Обновляем сценарий пользователя")
        try:
            stmt_update_user_status_scenario = update(scenario).where(scenario.c.user_id == user_id).values(scenario_state=json_sctructure)
            await session.execute(stmt_update_user_status_scenario)
        except exc.SQLAlchemyError as e:
            logging.error(e)

    @staticmethod
    async def is_report_occupied(report_id:int, session:AsyncSession) -> bool:
        logging.info("Проверяем жалобу на занятость")
        scenario_with_report_id = None
        try:
            stmt_find_scenario_with_report_id = select(scenario).where(cast(scenario.c.scenario_state.op('->>')('report_id'), Integer) == report_id)
            scenario_with_report_id = await session.execute(stmt_find_scenario_with_report_id)
        except exc.SQLAlchemyError as e:
            logging.error(e)
        return bool(scenario_with_report_id.all())