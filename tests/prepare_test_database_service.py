from classes import chatgpt_person
from src.database.classes import chat_service, chatgpt_chat_service, operation_state_service, punishment_service
from src.database.classes import report_service, user_in_search_service, user_service, scenario_service
from user_operation.schemas.databaseschemas import ChatGPTPerson, User
from user_operation.schemas.databaseschemas import Punishment
from database.models import Punishment_type, Reason_type
from user_operation.schemas.databaseschemas import Report, SolvedReport, Scenario, UserInSearch
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Role_type, User_state, User_filter
import logging
from datetime import datetime
from user_operation.schemas.databaseschemas import Chat

class TestDabaseManager:
    async def prepare_database(self, session:AsyncSession):
        try:
            await self.prepare_users(session=session)
            await self.prepare_chats(session=session)
            await self.prepare_reports(session=session)
            await self.prepare_punishments(session=session)
            await self.prepare_scenario(session=session)
            await self.prepare_chatgpt_chats(session=session)
            await self.prepare_user_in_search(session=session)
        except Exception as e:
            logging.error(e)

    async def prepare_users(self, session:AsyncSession):
        add_user = user_service.UserService.add_new_user
        new_user = None
        for id in range(100, 111):
            new_user = User(
                    id = id,
                    registered_at = datetime(2024, 1, 1, 0, 0, 0, 0),
                    role_id = Role_type.user,
                    connected_user = -1,
                    prev_chat_id = -1,
                    state = User_state.menu_state,
                    username = f'test{id}'
                )
            await add_user(new_user, session)
        
        new_user.id = 8888

        await add_user(new_user, session)

        add_admin = user_service.UserService.change_user_role
        await add_admin(101, Role_type.admin, session)
        await add_admin(102, Role_type.admin, session)
        await add_admin(109, Role_type.admin, session)
        await user_service.UserService.update_user_connected_user_and_chat_id(104, 105, 1, session)
        await user_service.UserService.update_user_connected_user_and_chat_id(105, 104, 1, session)

        await self.prepare_states(session)

    async def prepare_states(self, session:AsyncSession):
        change_state = user_service.UserService.change_user_state
        await change_state(100, session, User_state.admin_panel_state)
        await change_state(104, session, User_state.chatting_state)
        await change_state(105, session, User_state.chatting_state)

    async def prepare_chats(self, session:AsyncSession):
        add_chat = chat_service.ChatService.add_new_chat
        time = datetime(2024, 1, 1, 0, 0, 0, 0)

        new_chat = Chat(
            first_user_id = 104,
            second_user_id = 105,
            started_at = time,
        )

        await add_chat(new_chat, session)

        new_chat.first_user_id = 100
        new_chat.second_user_id = 101
        await add_chat(new_chat, session)

        new_chat.first_user_id = 103
        new_chat.second_user_id = 8888
        await add_chat(new_chat, session)

        new_chat.first_user_id = 102
        new_chat.second_user_id = 8888
        await add_chat(new_chat, session)

    async def prepare_punishments(self, session:AsyncSession):
        punish = punishment_service.PunishmentService.apply_punishment
        time = datetime(2024, 1, 1, 0, 0, 0, 0)
        for i in range (100, 111, 6):
            punishment = Punishment(
                user_id=i, 
                reason=Reason_type.insult,
                created_at=time,
                type_of_punishment=Punishment_type.ban,
                ended_at=time.replace(year=time.year + 100)
            )
            await punish(session, punishment)

    async def prepare_scenario(self, session:AsyncSession):
        add_scenario = scenario_service.ScenarioService.add_user_status_scenario
        time = datetime(2024, 1, 1, 0, 0, 0, 0)
        new_scenario = Scenario(
            user_id = 107,
            started_at = time,
            scenario_state = {'report_id':1}
        )
        await add_scenario(new_scenario, session)

    async def prepare_reports(self, session:AsyncSession):
        add_report = report_service.ReportService.add_new_report
        time = datetime(2024, 1, 1, 0, 0, 0, 0)
        new_report = Report(
                            chat_id = 2,
                            reason = Reason_type.insult,
                            user_id = 101,
                            user_commentary = "Оскорбление",
                            created_at = time
                        )
        await add_report(new_report, session)
        new_report.user_id = 100
        await add_report(new_report, session)
        new_report.chat_id = 1
        new_report.user_id = 105
        await add_report(new_report, session)
        new_report.chat_id = 3
        new_report.user_id = 103
        await add_report(new_report, session)
        new_report.chat_id = 4
        new_report.user_id = 102
        await add_report(new_report, session)

        add_solved_report = report_service.ReportService.add_solved_report
        
        await report_service.ReportService.delete_report(2, session)
        new_solved_report = SolvedReport(
                                id = 2,
                                chat_id = 1,
                                reason = Reason_type.insult,
                                user_id = 104,
                                user_commentary = "insult",
                                created_at = time,
                                solved_at = time,
                                admin_id_solved_report=109,
                                type_of_punishment = Punishment_type.ban,
                                admin_commentary = "insult"
                            )
        await add_solved_report(new_solved_report, session)

    async def prepare_user_in_search(self, session:AsyncSession):
        add_user_in_search = user_in_search_service.UserInSearchService.add_user_in_search
        
        time = datetime(2024, 1, 1, 0, 0, 0, 0)
        new_user_in_search = UserInSearch(
            user_id = 105,
            started_at = time,
            filter = User_filter.all
        )
        await add_user_in_search(new_user_in_search, session)

    async def prepare_chatgpt_chats(self, session:AsyncSession):
        gpt_person = ChatGPTPerson(
            user_id=102,
            chat_id=4,
            chatgpt_person='Ты – человек, который общается в анонимном чате. Используй непринужденный и разговорный стиль.'
        )
        add_chatgpt_chat = chatgpt_chat_service.ChatgptChatService.add_chatgpt_person
        await add_chatgpt_chat(gpt_person, session)

