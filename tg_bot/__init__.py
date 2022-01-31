import logging
import os
import sys

import telegram.ext as tg
from configparser import ConfigParser


def get_user_list(__init__, key):
    with open("{}/tg_bot/{}".format(os.getcwd(), __init__), "r") as json_file:
        return json.load(json_file)[key]


# enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler('log.txt'),
              logging.StreamHandler()],
    level=logging.INFO)

LOGGER = logging.getLogger(__name__)

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    LOGGER.error(
        "You MUST have a python version of at least 3.6! Multiple features depend on this. Bot quitting."
    )
    quit(1)

parser = ConfigParser()
parser.read("config.ini")
ahegaoconfig = parser["ahegaoconfig"]

TOKEN = ahegaoconfig.get("TOKEN")
OWNER_ID = ahegaoconfig.getint("OWNER_ID")
OWNER_USERNAME = ahegaoconfig.get("OWNER_USERNAME")
DB_URI = ahegaoconfig.get("SQLALCHEMY_DATABASE_URI")
DB_NAME = ahegaoconfig.get("SQLALCHEMY_DATABASE_URI")
MESSAGE_DUMP = ahegaoconfig.getfloat("MESSAGE_DUMP")
LOAD = ahegaoconfig.get("LOAD").split()
LOAD = list(map(str, LOAD))
NO_LOAD = ahegaoconfig.get("NO_LOAD").split()
NO_LOAD = list(map(str, NO_LOAD))
WEBHOOK = ahegaoconfig.getboolean("WEBHOOK", False)
URL = ahegaoconfig.get("URL", None)
DEV_USERS = get_user_list("elevated_users.json", "devs")
SUDO_USERS = get_user_list("elevated_users.json", "sudos")
SUPPORT_USERS = get_user_list("elevated_users.json", "supports")
WHITELIST_USERS = get_user_list("elevated_users.json", "whitelists")
CERT_PATH = ahegaoconfig.get("CERT_PATH", None)
PORT = ahegaoconfig.getint("PORT", None)
INFOPIC = ahegaoconfig.getboolean("INFOPIC", False)
DEL_CMDS = ahegaoconfig.getboolean("DEL_CMDS", False)
STRICT_GBAN = ahegaoconfig.getboolean("STRICT_GBAN", False)
STRICT_GMUTE = ahegaoconfig.getboolean("STRICT_GMUTE", False)
WORKERS = ahegaoconfig.getint("WORKERS")
BAN_STICKER = ahegaoconfig.get("BAN_STICKER", None)
ALLOW_EXCL = ahegaoconfig.getboolean("ALLOW_EXCL", False)
SUPPORT_CHAT = ahegaoconfig.get("SUPPORT_CHAT", None)
START_STICKER = ahegaoconfig.get("START_STICKER", None)
LOGS = ahegaoconfig.getfloat("LOGS", None)
BACKUP_PASS = ahegaoconfig.get("BACKUP_PASS")
IGNORE_PENDING_REQUESTS = ahegaoconfig.getboolean("IGNORE_PENDING_REQUESTS", False)

DEV_USERS.append(OWNER_ID)
SUDO_USERS.append(OWNER_ID)

updater = tg.Updater(TOKEN, workers=WORKERS)

dispatcher = updater.dispatcher

CallbackContext = tg.CallbackContext

SUDO_USERS = list(SUDO_USERS)
WHITELIST_USERS = list(WHITELIST_USERS)
SUPPORT_USERS = list(SUPPORT_USERS)

# Load at end to ensure all prev variables have been set
from tg_bot.modules.helper_funcs.handlers import CustomCommandHandler, CustomRegexHandler, CustomMessageHandler

tg.RegexHandler = CustomRegexHandler
tg.MessageHandler = CustomMessageHandler

if ALLOW_EXCL:
    tg.CommandHandler = CustomCommandHandler
