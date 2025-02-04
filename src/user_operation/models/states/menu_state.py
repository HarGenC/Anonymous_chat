from database.classes import report_service, scenario_service, user_service
from database.database import get_async_session
import logging
import telebot
import json
from datetime import datetime
from user_operation.schemas.databaseschemas import Scenario
from user_operation.schemas.databaseschemas import Report
from user_operation.models.states import current_state as cs
from user_operation.models.states import in_searching_state
from user_operation.models.states import admin_panel_state
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from database.models import User_state, Reason_type
from user_operation.models import user_state_machine as usm

class MenuState(cs.CurrentState):
    def __init__(self):
        super().__init__()
        self.register_commands()

    async def enter_state(self, user_manager:usm.UserStateManager):
        logging.info("Пользователь вошёл в состояние главного меню")
        user_id = user_manager.message.from_user.id
        reply_markup = self.create_starting_menu_keyboard(is_admin=user_manager.is_admin)
        try:
            await user_manager.bot.send_message(chat_id=user_id, text="Вы в главном меню", reply_markup=reply_markup)
        except telebot.apihelper.ApiException as e:
            logging.error(e)

    async def update_state(self, user_manager:usm.UserStateManager):
        user_status = None
        async for session in get_async_session():
            user_status = await scenario_service.ScenarioService.get_user_status_scenario(user_id=user_manager.message.from_user.id, session=session)

        if not user_status == None:
            await self.commands.get(user_status["status"])(user_manager, user_status["status"])

        elif user_manager.message.text in self.commands:
            await self.commands.get(user_manager.message.text)(user_manager)

    async def is_state(self):
        return User_state.menu_state

    def register_commands(self):
        # Регистрация команд через вызов декоратора
        self.command("Пожаловаться")(self.get_report_menu)
        self.command("Начать поиск")(self.start_search)
        self.command("Открыть панель админа")(self.open_admin_panel)

    async def add_report_scenario(self, user_manager:usm.UserStateManager, bot_answer:str):
        async for session in get_async_session():
            async with session.begin():
                scenario_state = {"status": user_manager.message.text}
                new_scenario = None
                try:
                    new_scenario = Scenario(
                        user_id = user_manager.message.from_user.id,
                        started_at = datetime.utcnow(),
                        scenario_state = scenario_state
                    )
                except Exception as e:
                    logging.error(e)
                await scenario_service.ScenarioService.add_user_status_scenario(new_scenario=new_scenario, session=session)
                try:
                    await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, text=bot_answer, reply_markup=self.create_report_keyboard())
                except telebot.apihelper.ApiException as e:
                    logging.error(e)

    def create_report_keyboard(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Оскорбление"))
        markup.add(KeyboardButton("Вернуться в меню"))
        return markup

    async def get_report_menu(self, user_manager:usm.UserStateManager, scenario:json = {}):
        async for session in get_async_session():
            if await user_service.UserService.get_current_chat(user_id=user_manager.message.from_user.id, session=session) == -1:
                await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                    text="Вы ещё не общались")
                return
            if await report_service.ReportService.is_reported(user_id=user_manager.message.from_user.id, session=session):
                await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                    text="Вы уже жаловались")
                return
            
        if scenario == {}:
            await self.add_report_scenario(user_manager=user_manager,
                                           bot_answer="Выберите жалобу из списка ниже или напишите самостоятельно причину жалобы")
            return
        
        if user_manager.message.text == "Вернуться в меню":
            async for session in get_async_session():
                async with session.begin():
                    await scenario_service.ScenarioService.delete_user_status_scenario(user_id=user_manager.message.from_user.id, session=session)
            await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                text="Вы вернулись в главное меню", 
                                                reply_markup=self.create_starting_menu_keyboard(user_manager.is_admin))
        else:
            reason = Reason_type.other
            if user_manager.message.text == "Оскорбление":
                reason = Reason_type.insult
            async for session in get_async_session():
                async with session.begin():
                    user = await user_service.UserService.get_user_from_db(user_id=user_manager.message.from_user.id, 
                                                            session=session)
                    new_report = None
                    try:
                        new_report = Report(
                            chat_id = user[0][4],
                            reason = reason,
                            user_id = user_manager.message.from_user.id,
                            user_commentary = user_manager.message.text,
                            created_at = datetime.utcnow()
                        )
                    except Exception as e:
                        logging.error(e)
                    await report_service.ReportService.add_new_report(new_report=new_report, 
                                                                      session=session)
                    await scenario_service.ScenarioService.delete_user_status_scenario(user_id=user_manager.message.from_user.id, session=session)
            await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                text="Вы успешно пожаловались", 
                                                reply_markup=self.create_starting_menu_keyboard(user_manager.is_admin))


    async def start_search(self, user_manager:usm.UserStateManager):
        await user_manager.switch_state(in_searching_state.InSearchingState())

    async def open_admin_panel(self, user_manager:usm.UserStateManager):
        if not user_manager.is_admin:
            return
        
        async for session in get_async_session():
            async with session.begin():
                await user_service.UserService.change_user_state(user_id=user_manager.message.from_user.id, session=session, user_state=User_state.admin_panel_state)
            await user_manager.switch_state(admin_panel_state.AdminPanelState())

    def create_starting_menu_keyboard(self, is_admin:bool) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Начать поиск"))
        markup.add(KeyboardButton("Пожаловаться"))
        if is_admin:
            markup.add(KeyboardButton("Открыть панель админа"))
        return markup
    