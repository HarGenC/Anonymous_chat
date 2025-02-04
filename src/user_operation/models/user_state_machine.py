from telebot.async_telebot import AsyncTeleBot

from user_operation.models.states import current_state as cs
from classes import message as msg

class UserStateManager:
    current_state:cs.CurrentState
    is_admin:bool
    is_super_user:bool

    message:msg.Message
    bot:AsyncTeleBot

    def __init__(self, current_state:cs.CurrentState, message:msg.Message, is_admin:bool, is_super_user:bool, bot:AsyncTeleBot):
        self.current_state = current_state
        self.is_admin = is_admin
        self.is_super_user = is_super_user
        self.message = message
        self.bot = bot
        

    async def switch_state(self, current_state:cs.CurrentState):
        self.current_state = current_state
        await self.current_state.enter_state(user_manager=self)

    async def update(self):
        await self.current_state.update_state(user_manager=self)

