from database import models
from user_operation.models.states import admin_panel_state
from user_operation.models.states import chatting_state
from user_operation.models.states import in_searching_state
from user_operation.models.states import menu_state

class_map = {
    models.User_state.in_searching_state: in_searching_state.InSearchingState,
    models.User_state.chatting_state: chatting_state.ChattingState,
    models.User_state.menu_state: menu_state.MenuState,
    models.User_state.admin_panel_state: admin_panel_state.AdminPanelState,
}