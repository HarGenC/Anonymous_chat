import enum
from sqlalchemy import MetaData, Table, Column, Integer, String, TIMESTAMP, ForeignKey, JSON, Enum
from datetime import datetime
from database.database import metadata

class Reason_type(enum.Enum):
    insult = 0
    other = 999

class Punishment_type(enum.Enum):
    ban = 0
    other = 999

class Role_type(enum.Enum):
    admin = 0
    user = 1

class User_filter(enum.Enum):
    all = 0

class User_state(enum.Enum):
    in_searching_state = 0
    chatting_state = 1
    menu_state = 2
    admin_panel_state = 3

user = Table(
    "user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("registered_at", TIMESTAMP, default=datetime.utcnow),
    Column("role_id", Enum(Role_type), default=1),
    Column("connected_user", Integer, nullable=True),
    Column("prev_chat_id", Integer, nullable=True),
    Column("state", Enum(User_state), default=0),
    Column("username", String, nullable=True)
)

chat = Table(
    "chat",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("first_user_id", Integer, ForeignKey("user.id")),
    Column("second_user_id", Integer, ForeignKey("user.id")),
    Column("started_at", TIMESTAMP, default=datetime.utcnow),
    Column("finished_at", TIMESTAMP, nullable=True)
)

report = Table(
    "report",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("chat_id", Integer, ForeignKey("chat.id")),
    Column("reason", Enum(Reason_type), nullable=False),
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("user_commentary", String, default=""),
    Column("created_at", TIMESTAMP, nullable = False)
)

solved_report = Table(
    "solved_report",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("chat_id", Integer, ForeignKey("chat.id")),
    Column("reason", Enum(Reason_type), nullable=False),
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("user_commentary", String, default=""),
    Column("created_at", TIMESTAMP, nullable = False),
    Column("solved_at", TIMESTAMP, nullable = False),
    Column("admin_id_solved_report", Integer, ForeignKey("user.id")),
    Column("type_of_punishment", Enum(Punishment_type), nullable=False),
    Column("admin_commentary", String, nullable=True),
)

punishment = Table(
    "punishment",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("reason", Enum(Reason_type), nullable=True),
    Column("created_at", TIMESTAMP, default=datetime.utcnow),
    Column("type_of_punishment", Enum(Punishment_type), nullable=True),
    Column("ended_at", TIMESTAMP, nullable=False)
)

user_in_search = Table(
    "user_in_search",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("started_at", TIMESTAMP, nullable=False),
    Column("filter", Enum(User_filter), nullable=False)
)

scenario = Table(
    "scenario",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("started_at", TIMESTAMP, nullable=False),
    Column("scenario_state", JSON, nullable=True)
)

chatgpt_chat = Table(
    "chatgpt_chat",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("chat_id", Integer, ForeignKey("chat.id")),
    Column("chatgpt_person", String, nullable=False)
)
