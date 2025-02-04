from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

DB_HOST_TEST = os.environ.get("DB_HOST_TEST")
DB_PORT_TEST = os.environ.get("DB_PORT_TEST")
DB_NAME_TEST = os.environ.get("DB_NAME_TEST")
DB_USER_TEST = os.environ.get("DB_USER_TEST")
DB_PASS_TEST = os.environ.get("DB_PASS_TEST")

API_CHATGPT_KEY = os.environ.get("API_CHATGPT_KEY")
API_CHATBOT_KEY = os.environ.get("API_CHATBOT_KEY")
SUPER_USER_ID = os.environ.get("SUPER_USER_ID")
CHATGPT_USER_ID = os.environ.get("CHATGPT_USER_ID")

LOCALIP = os.environ.get("lOCALIP")
LOCALPORT = os.environ.get("LOCALPORT")

PATH_SSL_KEYFILE= os.environ.get("PATH_SSL_KEYFILE")
PATH_SSL_CERTIFILE = os.environ.get("PATH_SSL_CERTIFILE")