from config import SUPER_USER_ID
import start_config
from telebot.async_telebot import AsyncTeleBot
from database.classes.scenario_service import ScenarioService
from database.classes.punishment_service import PunishmentService
from database.classes.user_service import UserService
from database.database import get_async_session
from user_operation.models import user_state_machine as usm
from user_operation.models.states import admin_panel_state
from user_operation.models.states import in_searching_state
from user_operation.models.states import chatting_state
from classes import message as msg
import logging

class OperationStateService:
    @staticmethod
    async def get_user_state_manager(user_id:int, bot:AsyncTeleBot, mymessage:msg.Message) -> usm.UserStateManager:
        logging.info("Получаем менеджера состояния пользователя")
        current_state = None
        is_admin = False
        is_super_user = False

        async for session in get_async_session():
            current_state = await UserService.get_user_state(user_id=user_id, session=session)

        if user_id == int(SUPER_USER_ID):
            is_admin = True
            is_super_user = True
        else:
            async for session in get_async_session():
                is_admin = await UserService.is_user_admin(user_id=user_id, session=session)
        
        return usm.UserStateManager(start_config.class_map.get(current_state)(), message=mymessage,
                                is_admin=is_admin, is_super_user=is_super_user, bot=bot)

    @staticmethod
    async def quit_from_admin_panel_state(user_state_manager:usm.UserStateManager) -> bool:
        if isinstance(user_state_manager.current_state, admin_panel_state.AdminPanelState):
            logging.info("Выходим из состояния админской панели")
            async for session in get_async_session():
                async with session.begin():
                    user_status = await ScenarioService.get_user_status_scenario(user_id=user_state_manager.message.from_user.id, session=session)
                    if not user_status == {}:
                        await ScenarioService.delete_user_status_scenario(user_id=user_state_manager.message.from_user.id, session=session)
            await admin_panel_state.AdminPanelState().quit(user_manager=user_state_manager)
            return True
        return False

    @staticmethod
    async def quit_from_in_searching_state(user_state_manager:usm.UserStateManager) -> bool:
        if isinstance(user_state_manager.current_state, in_searching_state.InSearchingState):
            logging.info("Выходим из состояния в поиске")
            await in_searching_state.InSearchingState().finish_searching(user_manager=user_state_manager)
            return True
        return False

    @staticmethod
    async def quit_and_answer_from_chatting_state(user_state_manager:usm.UserStateManager, bot_answer:str) -> bool:
        if isinstance(user_state_manager.current_state, chatting_state.ChattingState):
            logging.info("Выходим из состояния общения в чате")
            user_state_manager.message.text = bot_answer
            await user_state_manager.update()
            await chatting_state.ChattingState().finish_chat(user_manager=user_state_manager)
            return True
        return False

    @staticmethod
    async def quit_from_all_state_in_menu(user_state_manager:usm.UserStateManager, bot_answer:str):
        logging.info("Выходим из всех состояний в главное меню")
        if await OperationStateService.quit_from_admin_panel_state(user_state_manager=user_state_manager):
            return True
        if await OperationStateService.quit_from_in_searching_state(user_state_manager=user_state_manager):
            return True
        if await OperationStateService.quit_and_answer_from_chatting_state(user_state_manager=user_state_manager, bot_answer=bot_answer):
            return True
        return False

    @staticmethod
    async def check_and_update_admin_panel_state(user_state_manager:usm.UserStateManager) -> bool:
        logging.info("Проверяем и обновляем своё состояние в админской панели") # Возможно стоит ещё подумать тут
        if user_state_manager.is_admin:
            return False
        return await OperationStateService.quit_from_admin_panel_state(user_state_manager=user_state_manager)

    @staticmethod
    async def check_and_update_in_searching_state(user_state_manager:usm.UserStateManager, is_banned:bool) -> bool:
        logging.info("Проверяем и обновляем своё состояние в поиске") # Возможно стоит ещё подумать тут
        if not is_banned:
            return False
        return await OperationStateService.quit_from_in_searching_state(user_state_manager=user_state_manager)

    @staticmethod
    async def check_and_update_chatting_state(user_state_manager:usm.UserStateManager, is_banned:bool, bot_answer:str) -> bool:
        logging.info("Проверяем и обновляем своё состояние в чате") # Возможно стоит ещё подумать тут
        if not is_banned:
            return False
        return await OperationStateService.quit_and_answer_from_chatting_state(user_state_manager=user_state_manager, bot_answer=bot_answer)

    @staticmethod
    async def check_and_update_all_important_states(user_state_manager:usm.UserStateManager, is_banned:bool, bot_answer:str):
        logging.info("Проверяем и обновляем все важные состояния") # Возможно стоит ещё подумать тут

        if await OperationStateService.check_and_update_admin_panel_state(user_state_manager=user_state_manager):
            return True

        if await OperationStateService.check_and_update_in_searching_state(user_state_manager=user_state_manager, is_banned=is_banned):
            return True


        if await OperationStateService.check_and_update_chatting_state(user_state_manager=user_state_manager,
                                                is_banned=is_banned, 
                                                bot_answer=bot_answer):
            return True
        return False

    @staticmethod
    async def check_and_update_current_user_state(user_id:int, bot:AsyncTeleBot):
        logging.info("Проверяем и обновляем текущее состояние пользователя") # Возможно стоит ещё подумать тут
        user_state_manager = await OperationStateService.get_user_state_manager(user_id=user_id, bot=bot, mymessage=msg.Message(text="null", id=user_id, msg_id=""))
        is_banned = False
        async for session in get_async_session():
            is_banned = await PunishmentService.is_user_punished(user_id=user_id, session=session)

        await OperationStateService.check_and_update_all_important_states(user_state_manager=user_state_manager,
                                                    is_banned=is_banned, 
                                                    bot_answer="К сожалению, ваш собеседник получил бан, вследствие чего ваш диалог прекращается")