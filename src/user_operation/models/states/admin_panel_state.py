from datetime import datetime 
import enum
import json
import logging
import telebot
import mimetypes
from user_operation.schemas.databaseschemas import Scenario
from database.models import Role_type
from user_operation.schemas.databaseschemas import Punishment, SolvedReport
from database.classes import chat_service, operation_state_service, punishment_service, scenario_service, user_service, report_service
from database.models import Punishment_type, Reason_type
from user_operation.models.states.current_state import *
from user_operation.models import user_state_machine as usm
from user_operation.models.states import menu_state
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from database.database import get_async_session
from database.models import User_state
from classes import user_history_table
from classes import output_manager

class AdminPanelScenario(enum.Enum):
    ban_user = 0,
    unban_user = 1,
    view_report = 2,
    get_user_id_link = 3,
    add_admin = 4,
    demote_admin = 5

class AdminPanelState(CurrentState):
    def __init__(self):
        super().__init__()
        self.register_commands()

    async def enter_state(self, user_manager:usm.UserStateManager):
        try:
            await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id,
                                                text="Добро пожаловать в админскую панель", 
                                                reply_markup=self.create_admin_starting_keyboard(user_manager.is_super_user))
        except telebot.apihelper.ApiException as e:
            logging.error(e)

    async def update_state(self, user_manager:usm.UserStateManager):
        if not user_manager.is_admin:
            await self.quit(user_manager=user_manager)
        
        user_status = None
        async for session in get_async_session():
            user_status = await scenario_service.ScenarioService.get_user_status_scenario(user_id=user_manager.message.from_user.id, session=session)

        logging.debug(user_status)
        if not user_status == None:
            await self.commands.get(user_status["status"])(user_manager, user_status)

        elif user_manager.message.text in self.commands:
            await self.commands.get(user_manager.message.text)(user_manager)

    async def is_state(self):
        return User_state.admin_panel_state
    
    def register_commands(self):
        # Регистрация команд через вызов декоратора
        self.command("Забанить пользователя по его id")(self.ban_user)
        self.command("Разбанить пользователя по его id")(self.unban_user)
        self.command("Посмотреть id нерешённых жалоб")(self.get_unsolved_reports)
        self.command("Посмотреть определённую жалобу")(self.view_report)
        self.command("Решить определённую жалобу")(self.solve_report)
        self.command("Получить ссылку на пользователя по его id")(self.get_user_id_link)
        self.command("Добавить админа")(self.add_admin)
        self.command("Удалить админа")(self.demote_admin)
        self.command("Выйти из админской панели")(self.quit)

    def create_admin_starting_keyboard(self, is_super_user:bool) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Забанить пользователя по его id"))
        markup.add(KeyboardButton("Разбанить пользователя по его id"))
        markup.add(KeyboardButton("Посмотреть id нерешённых жалоб"))
        markup.add(KeyboardButton("Посмотреть определённую жалобу"))
        markup.add(KeyboardButton("Решить определённую жалобу"))
        markup.add(KeyboardButton("Получить ссылку на пользователя по его id"))
        if is_super_user:
            markup.row(KeyboardButton("Добавить админа"), KeyboardButton("Удалить админа"))
        markup.add(KeyboardButton("Выйти из админской панели"))
        return markup
    
    def create_quit_keyboard(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Вернуться в меню"))
        return markup
    

    def create_punishment_keyboard(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Забанить"))
        markup.add(KeyboardButton("Не банить"))
        markup.add(KeyboardButton("Получить историю диалога"))
        markup.add(KeyboardButton("Получить файлы диалога"))
        markup.add(KeyboardButton("Вернуться в меню"))
        return markup
    
    def create_commentary_keyboard(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Оскорбление"))
        markup.add(KeyboardButton("Нет причин для бана"))
        markup.add(KeyboardButton("Вернуться в меню"))
        return markup
    
    async def add_scenario(self, user_manager:usm.UserStateManager, bot_answer:str):
        logging.info("Добавления начального статуса сценария")
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
                    await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, text=bot_answer, reply_markup=self.create_quit_keyboard())
                except telebot.apihelper.ApiException as e:
                    logging.error(e)

    async def is_id_answer_scenario(self, user_manager:usm.UserStateManager) -> bool: #Нужно функцию разбить
        logging.info("проверка, что ответ пользователя число")
        if user_manager.message.text.isdigit():
            return True
        if not user_manager.message.text == "Вернуться в меню":
            try:
                await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                    text="Нужен id")
                return False
            except telebot.apihelper.ApiException as e:
                logging.error(e)

        else:
            try:
                await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                    text="Вы вернулись в меню", 
                                                    reply_markup=self.create_admin_starting_keyboard(user_manager.is_super_user))
            except telebot.apihelper.ApiException as e:
                logging.error(e)

        async for session in get_async_session():
            async with session.begin():
                await scenario_service.ScenarioService.delete_user_status_scenario(user_id=user_manager.message.from_user.id, session=session)
        return False

    async def ban_user(self, user_manager:usm.UserStateManager, scenario:json = {}):
        if scenario == {}:
            logging.info("Заход в сценарий забанить пользователя")
            await self.add_scenario(user_manager=user_manager, bot_answer="Введите id пользователя")
            return

        if not await self.is_id_answer_scenario(user_manager=user_manager):
            return
        logging.info("Попытка забанить пользователя")
        async for session in get_async_session():
            async with session.begin():
                try:
                    if not await user_service.UserService.is_there_user(user_id=int(user_manager.message.text), session=session):
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                            text="Такого пользователя не существует в базе данных")
                        return
                    if await punishment_service.PunishmentService.is_user_punished(user_id=int(user_manager.message.text), session=session):
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                            text="Этот пользователь уже забанен")
                        return
                    if await user_service.UserService.is_user_admin(user_id=int(user_manager.message.text), session=session):
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                            text="Вы не можете забанить админа")
                        return
                except telebot.apihelper.ApiException as e:
                    logging.error(e)

                new_punishment = Punishment(
                    user_id = int(user_manager.message.text),
                    reason = Reason_type.other,
                    created_at = datetime.utcnow(),
                    type_of_punishment = Punishment_type.ban,
                    ended_at = datetime.utcnow().replace(year=datetime.utcnow().year + 100)
                )

                await punishment_service.PunishmentService.apply_punishment(punishment=new_punishment, session=session)
                try:
                    await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                        text="Поздравляю вы успешно забанили пользователя",
                                                        reply_markup=self.create_admin_starting_keyboard(user_manager.is_super_user))
                except telebot.apihelper.ApiException as e:
                    logging.error(e)
                await scenario_service.ScenarioService.delete_user_status_scenario(user_id=user_manager.message.from_user.id, session=session)
        async for session in get_async_session():
            async with session.begin():
                await operation_state_service.OperationStateService.check_and_update_current_user_state(user_id=int(user_manager.message.text),
                                                                                                        bot=user_manager.bot)
            
    async def unban_user(self, user_manager:usm.UserStateManager, scenario:json = {}):
        if scenario == {}:
            logging.info("Заход в сценарий разбанить пользователя")
            await self.add_scenario(user_manager=user_manager, bot_answer="Введите id пользователя")
            return
        
        if not await self.is_id_answer_scenario(user_manager=user_manager):
            return
        
        logging.info("Попытка разбанить пользователя")
        async for session in get_async_session():
            async with session.begin():
                try:
                    if not await user_service.UserService.is_there_user(user_id=int(user_manager.message.text), session=session):
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                            text="Такого пользователя не существует в базе данных")
                        return
                    if not await punishment_service.PunishmentService.is_user_punished(user_id=int(user_manager.message.text), session=session):
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                            text="Этот пользователь не забанен")
                        return
                except telebot.apihelper.ApiException as e:
                    logging.error(e)
                    
                await punishment_service.PunishmentService.delete_punishment_with_user_id(user_id=int(user_manager.message.text), session=session)
                try:
                    await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                        text="Поздравляю вы успешно разбанили пользователя",
                                                        reply_markup=self.create_admin_starting_keyboard(user_manager.is_super_user))
                except telebot.apihelper.ApiException as e:
                    logging.error(e)
                await scenario_service.ScenarioService.delete_user_status_scenario(user_id=user_manager.message.from_user.id, session=session)
    
    async def view_report(self, user_manager:usm.UserStateManager, scenario:json = {}):
        if scenario == {}:
            logging.info("Заход в сценарий просмотра жалобы")
            await self.add_scenario(user_manager=user_manager, bot_answer="Введите id жалобы")
            return
        
        if not await self.is_id_answer_scenario(user_manager=user_manager):
            return
        
        async for session in get_async_session():
            async with session.begin():
                report = await report_service.ReportService.get_report(report_id=int(user_manager.message.text),session=session)
                if not bool(report):
                    try:
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                            text="Такой жалобы с таким id не существует")
                    except telebot.apihelper.ApiException as e:
                        logging.error(e)
                    return
                report = report[0]
                report_text = f"id: {report[0]}\nchat_id: {report[1]}\nreason: {report[2]}\n" \
                    + f"user_id: {report[3]}\nuser_commentary: {report[4]}\ncreated_at: {report[5]}"
                    
                if len(report) == 6:
                    try:
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                            text=report_text)
                    except telebot.apihelper.ApiException as e:
                        logging.error(e)
                        
                elif len(report) == 10:
                    report_text = report_text + f"\nsolved_at: {report[6]}\nadmin_id_solved_report: {report[7]}\n" \
                    + f"type_of_punishment: {report[8]}\nadmin_commentary: {report[9]}"
                    
                    try:
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                            text=report_text)
                    except telebot.apihelper.ApiException as e:
                        logging.error(e)

    async def get_unsolved_reports(self, user_manager:usm.UserStateManager):
        logging.info("Получение нерешённых жалоб")
        unsolved_reports = ""
        async for session in get_async_session():
            rows_unsolved_reports = await report_service.ReportService.get_n_unsolved_reports(session=session, n=5)

        if rows_unsolved_reports == None:
            unsolved_reports = 'Нерешённых жалоб нет'

        else:
            for report in rows_unsolved_reports:
                unsolved_reports += f"id: {report[0]}\nchat_id: {report[1]}\nreason: {report[2]}\n" \
                            + f"user_id: {report[3]}\nuser_commentary: {report[4]}\ncreated_at: {report[5]}\n"
        logging.debug(unsolved_reports)

        try:
            await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, text=unsolved_reports)
        except telebot.apihelper.ApiException as e:
            logging.error(e)

    async def get_history_chat(self, user_manager:usm.UserStateManager, report_id:int):
        logging.info("Получение истории чата")
        first_user_history_manager = user_history_table.UserHistoryTableManager(user_id=user_manager.message.from_user.id)

        async for session in get_async_session():
            report = await report_service.ReportService.get_report(report_id=report_id, session=session)
            chat_id = report[0][1]
            history = await first_user_history_manager.get_user_history_in_chat(chat_id=chat_id, session=session)
            output_text_manager = output_manager.OutputManager(history)
            data = await output_text_manager.do_json_format_output()
            try:
                with open("history_file.json", 'w', encoding='utf-8') as json_file: # Обработка ошибок
                    json.dump(data, json_file, indent=2, ensure_ascii=False)
                with open("history_file.json", 'rb') as json_file:
                    try:
                        await user_manager.bot.send_document(chat_id=user_manager.message.from_user.id, document=json_file)
                    except telebot.apihelper.ApiException as e:
                        logging.error(e)
            except OSError as e:
                logging.error(e)

    async def get_files_chat(self, user_manager:usm.UserStateManager, report_id:int):
        logging.info("Получение файлов из чата")
        first_user_history_manager = user_history_table.UserHistoryTableManager(user_id=user_manager.message.from_user.id)

        async for session in get_async_session():
            report = await report_service.ReportService.get_report(report_id=report_id, session=session)
            chat_id = report[0][1]
            history = await first_user_history_manager.get_user_history_in_chat(chat_id=chat_id, session=session)

            counter = 0
            for message in history:
                if message[3] == "None":
                    continue
                counter += 1

                file_url = await user_manager.bot.get_file_url(message[3])
                print(file_url)
                mime_type, _ = mimetypes.guess_type(file_url)
                try:
                    if mime_type.startswith('image/'):
                        await user_manager.bot.send_photo(chat_id=user_manager.message.from_user.id,
                                                    photo=message[3],
                                                    caption=f'file_{counter}')
                    elif mime_type.startswith('audio/'):
                        await user_manager.bot.send_audio(chat_id=user_manager.message.from_user.id,
                                                          audio=message[3],
                                                          caption=f'file_{counter}')
                    elif mime_type.startswith('video/'):
                        await user_manager.bot.send_video(chat_id=user_manager.message.from_user.id,
                                                          video=message[3],
                                                          caption=f'file_{counter}',
                                                          supports_streaming=True)
                    elif mime_type.startswith(tuple(['application/', 'text/'])):
                        await user_manager.bot.send_document(chat_id=user_manager.message.from_user.id,
                                                             document=message[3],
                                                             caption=f'file_{counter}')
                    elif mime_type.startswith(tuple(['application/', 'text/'])):
                        await user_manager.bot.send_voice(chat_id=user_manager.message.from_user.id,
                                                          voice=message[3],
                                                          caption=f'file_{counter}')
                except telebot.apihelper.ApiException as e:
                    logging.error(e)


    async def solve_report_get_report_id(self, user_manager:usm.UserStateManager, scenario:json):
        logging.info("Сценарий решение жалобы, ввод id жалобы")
        try:
            async for session in get_async_session():
                if not await report_service.ReportService.is_there_unsolved_report(int(user_manager.message.text), session=session):
                    await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                        text="Такой id нерешённой жалобы нет")
                    return
                if await scenario_service.ScenarioService.is_report_occupied(int(user_manager.message.text), session=session):
                    await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                        text="Эту жалобу уже решает другой админ")
                    return
        except telebot.apihelper.ApiException as e:
            logging.error(e)

        scenario['report_id'] = int(user_manager.message.text)
        async for session in get_async_session():
            async with session.begin():
                await scenario_service.ScenarioService.update_user_status_scenario(user_id=user_manager.message.from_user.id,
                                                                                    json_sctructure=scenario,
                                                                                    session=session)
                        
        report = None
        async for session in get_async_session():
            report = await report_service.ReportService.get_report(report_id=int(user_manager.message.text), session=session)
        report = report[0]
        report_text = f"id: {report[0]}\nchat_id: {report[1]}\nreason: {report[2]}\n" \
                + f"user_id: {report[3]}\nuser_commentary: {report[4]}\ncreated_at: {report[5]}"
        try:
            await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                text=report_text)
            await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                text="Выберите действие", reply_markup=self.create_punishment_keyboard())
        except telebot.apihelper.ApiException as e:
            logging.error(e)


    async def solve_report_get_status_punishment(self, user_manager:usm.UserStateManager, scenario:json):
        logging.info("Сценарий решение жалобы, выбор наказания")

        if user_manager.message.text == "Забанить":
            scenario['status_punishment'] = "ban"

        elif user_manager.message.text == "Не банить":
            scenario['status_punishment'] = "nothing"


        elif await self.is_return_menu(user_manager=user_manager):
            return
        elif user_manager.message.text == "Получить историю диалога":
            await self.get_history_chat(user_manager=user_manager, report_id=scenario["report_id"])
            return
        elif user_manager.message.text == "Получить файлы диалога":
            await self.get_files_chat(user_manager=user_manager, report_id=scenario["report_id"])
            return
        else:
            try:
                await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                    text="Неверная команда")
            except telebot.apihelper.ApiException as e:
                logging.error(e)
            return
            
        async for session in get_async_session():
            async with session.begin():
                await scenario_service.ScenarioService.update_user_status_scenario(user_id=user_manager.message.from_user.id,
                                                                                   json_sctructure=scenario,
                                                                                   session=session)
        try:
            await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                text="Можете написать комментарий или выбрать ответ, или вернуться в меню", 
                                                reply_markup=self.create_commentary_keyboard())
        except telebot.apihelper.ApiException as e:
            logging.error(e)

    async def is_return_menu(self, user_manager:usm.UserStateManager) -> bool:
        if not user_manager.message.text == "Вернуться в меню":
            return False
        
        async for session in get_async_session():
            async with session.begin():
                await scenario_service.ScenarioService.delete_user_status_scenario(user_id=user_manager.message.from_user.id, session=session)
                try:
                    await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                        text="Вы вернулись в меню", 
                                                        reply_markup=self.create_admin_starting_keyboard(user_manager.is_super_user))
                except telebot.apihelper.ApiException as e:
                    logging.error(e)
                return True

    async def solve_report(self, user_manager:usm.UserStateManager, scenario:json = {}):
        if scenario == {}:
            logging.info("Заход в сценарий решение жалобы")
            await self.add_scenario(user_manager=user_manager, bot_answer="Введите id жалобы")
            return
        
        elif not 'report_id' in scenario:
            if not await self.is_id_answer_scenario(user_manager=user_manager):
                return
            
            await self.solve_report_get_report_id(user_manager=user_manager, scenario=scenario)
            return

        elif not 'status_punishment' in scenario:
            await self.solve_report_get_status_punishment(user_manager=user_manager, scenario=scenario)
            return
            
        logging.info("Сценарий решение жалобы, комментарий админа")
        if await self.is_return_menu(user_manager=user_manager):
            return
            
        report_id = int(scenario['report_id'])
        status_paunishment = None
        if scenario['status_punishment'] == "ban":
            status_paunishment = Punishment_type.ban
        else: 
            status_paunishment = Punishment_type.other
        admin_commentary = user_manager.message.text
        second_user_id = None
        is_admin = False

        async for session in get_async_session():
            async with session.begin():
                report = await report_service.ReportService.is_there_unsolved_report(report_id=report_id, session=session)
                report = report[0]
                solved_report = None
                try:
                    solved_report = SolvedReport(
                        id = report_id,
                        chat_id = report[1],
                        reason = report[2],
                        user_id = report[3],
                        user_commentary = report[4],
                        created_at = report[5],
                        solved_at = datetime.utcnow(),
                        admin_id_solved_report = user_manager.message.from_user.id,
                        type_of_punishment = status_paunishment,
                        admin_commentary = admin_commentary
                    )
                except Exception as e:
                    print(e)
                    logging.error(e)

                await report_service.ReportService.add_solved_report(new_solved_report=solved_report,
                                                                     session=session)
                await scenario_service.ScenarioService.delete_user_status_scenario(user_id=user_manager.message.from_user.id, session=session)

                if status_paunishment == Punishment_type.ban:
                    report = await report_service.ReportService.get_report(report_id=report_id, session=session)
                    second_user_id = await chat_service.ChatService.get_reported_user(report_id=report_id, session=session)
                    try:
                        is_admin = await user_service.UserService.is_user_admin(user_id=second_user_id, session=session)
                        if is_admin:
                            await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id,
                                                                text=f"К сожалению, пользователя, которого вы хотите забанить, является админом, обратитесь к главному админу по этому поводу вот id этого админа: {second_user_id}")

                        else:
                            new_punishment = Punishment(
                                user_id = second_user_id,
                                reason = report[0][2],
                                created_at = datetime.utcnow(),
                                type_of_punishment = status_paunishment,
                                ended_at = datetime.utcnow().replace(year=datetime.utcnow().year + 100)
                            )

                            await punishment_service.PunishmentService.apply_punishment(punishment=new_punishment,
                                                                                          session=session)
                    except telebot.apihelper.ApiException as e:
                        logging.error(e)
                await report_service.ReportService.delete_report(report_id=report_id, session=session)
        try:
            await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                text="Поздравляю с решением жалобы! Вы вернулись в меню", 
                                                reply_markup=self.create_admin_starting_keyboard(user_manager.is_super_user))
        except telebot.apihelper.ApiException as e:
            logging.error(e)

        if not(status_paunishment == Punishment_type.ban and not is_admin):
            return
        
        async for session in get_async_session():
            async with session.begin():
                await operation_state_service.OperationStateService.check_and_update_current_user_state(user_id=second_user_id,
                                                                                                        bot=user_manager.bot)
    
    async def get_user_id_link(self, user_manager:usm.UserStateManager, scenario:json = {}):
        if scenario == {}:
            logging.info("Заход в сценарий получение ссылки на пользователя")
            await self.add_scenario(user_manager=user_manager, bot_answer="Введите id пользователя")
            return
        
        if not await self.is_id_answer_scenario(user_manager=user_manager):
            return
        logging.info("Сценарий получение ссылки на пользователя, ввод id жалобы")

        try:
            async for session in get_async_session():
                async with session.begin():
                    if not await user_service.UserService.is_there_user(user_id=int(user_manager.message.text), session=session):
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                            text="Такого пользователя не существует в базе данных")
                        return
                    username = await user_service.UserService.get_username_with_user_id(user_id=int(user_manager.message.text), session=session)
                    await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                        text=username,
                                                        reply_markup=self.create_admin_starting_keyboard(user_manager.is_super_user))
                    await scenario_service.ScenarioService.delete_user_status_scenario(user_id=user_manager.message.from_user.id, session=session)
        except telebot.apihelper.ApiException as e:
            logging.error(e)

    async def add_admin(self, user_manager:usm.UserStateManager, scenario:json = {}):
        if not user_manager.is_super_user:
            return
        
        if scenario == {}:
            logging.info("Заход в сценарий добавление админа")
            await self.add_scenario(user_manager=user_manager, bot_answer="Введите id пользователя")
            return
        
        if not await self.is_id_answer_scenario(user_manager=user_manager):
            return
        
        async for session in get_async_session():
            async with session.begin():
                logging.info("Сценарий добавление админа, ввод id админа")
                try:
                    if not await user_service.UserService.is_there_user(user_id=int(user_manager.message.text), session=session):
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                                text="Такого пользователя не существует в базе данных")
                        return
                except telebot.apihelper.ApiException as e:
                    logging.error(e)
                await user_service.UserService.change_user_role(user_id=int(user_manager.message.text), type_of_role=Role_type.admin, session=session)
                try:
                    await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                        text="Поздравляю вы добавили нового админа",
                                                        reply_markup=self.create_admin_starting_keyboard(user_manager.is_super_user))
                except telebot.apihelper.ApiException as e:
                    logging.error(e)
                await scenario_service.ScenarioService.delete_user_status_scenario(user_id=user_manager.message.from_user.id, session=session)

    async def demote_admin(self, user_manager:usm.UserStateManager, scenario:json = {}):
        if not user_manager.is_super_user:
            return
        
        elif scenario == {}:
            logging.info("Заход в сценарий удаление админа")
            await self.add_scenario(user_manager=user_manager, bot_answer="Введите id пользователя")
            return
        elif not await self.is_id_answer_scenario(user_manager=user_manager):
            return
        
        async for session in get_async_session():
            async with session.begin():
                try:
                    logging.info("Сценарий удаление админа, ввод id админа")
                    if not await user_service.UserService.is_there_user(user_id=int(user_manager.message.text), session=session):
                        await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                            text="Такого пользователя не существует в базе данных")
                        return
                    await user_service.UserService.change_user_role(user_id=int(user_manager.message.text), type_of_role=Role_type.user, session=session)
                        
                    await user_manager.bot.send_message(chat_id=user_manager.message.from_user.id, 
                                                        text="Сочувствую, вы понизили админа в должности",
                                                        reply_markup=self.create_admin_starting_keyboard(user_manager.is_super_user))
                    await scenario_service.ScenarioService.delete_user_status_scenario(user_id=user_manager.message.from_user.id, session=session)
                except telebot.apihelper.ApiException as e:
                    logging.error(e)
        async for session in get_async_session():
            async with session.begin():
                await operation_state_service.OperationStateService.check_and_update_current_user_state(user_id=int(user_manager.message.text),
                                                                                                        bot=user_manager.bot)

    async def quit(self, user_manager:usm.UserStateManager):
        logging.info("Выход из админской панели")
        async for session in get_async_session():
            async with session.begin():
                await user_service.UserService.change_user_state(user_id=user_manager.message.from_user.id, session=session, user_state=User_state.menu_state)
        await user_manager.switch_state(menu_state.MenuState())