from abc import ABC, abstractmethod

class CurrentState(ABC):
    def __init__(self):
        self.commands = {}
        
    @abstractmethod
    async def enter_state(self, user_manager):
        pass

    @abstractmethod
    async def update_state(self, user_manager):
        pass

    @abstractmethod
    async def is_state(self):
        pass

    def command(self, name):
        """Декоратор для регистрации команды."""
        def decorator(func):
            self.commands[name] = func
            return func
        return decorator