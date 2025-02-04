from pydantic import BaseModel, ConfigDict
from datetime import datetime
from pydantic import SkipValidation
from typing import Any
import json
from database.models import Role_type, User_state, User_filter, Reason_type, Punishment_type

class User(BaseModel):
    id:int
    registered_at:datetime
    role_id:Role_type
    connected_user:int
    prev_chat_id:int
    state:User_state
    username:str

class Chat(BaseModel):
    first_user_id:int
    second_user_id:int
    started_at:datetime

class UserInSearch(BaseModel):
    user_id:int
    started_at:datetime
    filter:User_filter

class Scenario(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id:int
    started_at:datetime
    scenario_state:SkipValidation[Any] #json

class Punishment(BaseModel):
    user_id:int
    reason:Reason_type
    created_at:datetime
    type_of_punishment:Punishment_type
    ended_at:datetime

class Report(BaseModel):
    chat_id:int
    reason:Reason_type
    user_id:int
    user_commentary:str
    created_at:datetime

class SolvedReport(BaseModel):
    id:int
    chat_id:int
    reason:Reason_type
    user_id:int
    user_commentary:str
    created_at:datetime
    solved_at:datetime
    admin_id_solved_report:int
    type_of_punishment:Punishment_type
    admin_commentary:str

class UserMessageHistory(BaseModel):
    user_id:int
    time_sended_message:datetime
    file_id:str
    text:str
    state:User_state
    chat_id:int

class ChatGPTPerson(BaseModel):
    user_id:int
    chat_id:int
    chatgpt_person:str