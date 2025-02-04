from fastapi import FastAPI, Request
from config import LOCALIP, LOCALPORT, PATH_SSL_KEYFILE, PATH_SSL_CERTIFILE
from telebot.types import Update
import uvicorn
from contextlib import asynccontextmanager
from database.classes.user_in_search_service import UserInSearchService
from database.database import get_async_session
from user_operation import router as rout
import asyncio
import random
from datetime import datetime
from chatGPT import operations
import logging
from logging.handlers import TimedRotatingFileHandler

# Настройка обработчика для ротации по времени
handler = TimedRotatingFileHandler('my_log_file.log', when='H', interval=1, backupCount=72)

import contextvars
import uuid

# Создаем контекстную переменную для trace id
trace_id_var = contextvars.ContextVar('trace_id', default="N/A")

# Кастомный форматтер, который добавляет trace_id
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Добавляем trace_id к записи логов
        record.trace_id = trace_id_var.get()
        return super().format(record)

for handler in logging.getLogger().handlers:
    handler.setFormatter(CustomFormatter(handler.formatter._fmt))

def set_trace_id(trace_id):
    trace_id_var.set(trace_id)

logging.basicConfig(
    level=logging.CRITICAL, #INFO
    datefmt="%Y-%m-%d %H:%M:%S",
    format="[%(asctime)s.%(msecs)03d] %(module)25s:%(lineno)-3d %(process)7d %(levelname)-7s - %(message)s - trace_id=%(trace_id)s",
    handlers=[handler]
    )


app = FastAPI(
    title="Online Anonymous Chat"
)
time = 3600 + random.random() * 3600
counter = 0

async def check_database():
    logging.info("Соединяем чатГПТ с пользователем с подходящим временем ожидания")
    async for session in get_async_session():
        async with session.begin():
            user_in_search = await UserInSearchService.get_user_in_search_with_the_longest_time(session=session)
            if user_in_search == None:
                return
            
            user_started_at = user_in_search[2].timestamp()
            now = datetime.utcnow().timestamp()
            global time
            if now - user_started_at > time:
                await operations.connect_with_chatGPT(user_id=user_in_search[1], bot=rout.bot, session=session)
                time = 600 + random.random() * 600

@app.post("/webhook")
async def receive_update(request: Request):
    set_trace_id(str(uuid.uuid4()))
    global counter
    counter += 1
    logging.info(f'Сообщение: {counter}')
    # Получаем JSON данные из запроса
    json_data = await request.json()
    update = await asyncio.to_thread(Update.de_json, json_data)
    await rout.bot.process_new_updates([update])
    # Здесь можно добавить логику обработки запроса
    # Например, отправка ответа пользователю или выполнение команды
    return {"status": "ok"}

async def run_periodically():
    while True:
        print("check")
        await check_database()
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(run_periodically())
    yield
    logging.shutdown()


if __name__ == "__main__":
    uvicorn.run("main:app", host=str(LOCALIP), port=int(LOCALPORT), ssl_keyfile=str(PATH_SSL_KEYFILE), ssl_certfile=str(PATH_SSL_CERTIFILE), reload=True)