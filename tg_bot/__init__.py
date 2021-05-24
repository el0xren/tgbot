import logging
import os
import sys

import telegram.ext as tg

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

ENV = bool(os.environ.get('ENV', False))

if ENV:
    TOKEN = os.environ.get('TOKEN', None)
    try:
        OWNER_ID = int(os.environ.get('OWNER_ID', None))
    except ValueError:
        raise Exception("Your OWNER_ID env variable is not a valid integer.")

    MESSAGE_DUMP = os.environ.get('MESSAGE_DUMP', None)
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", None)

    try:
        DEV_USERS = set(
            int(x) for x in os.environ.get("DEV_USERS", "").split())
        SUDO_USERS = set(
            int(x) for x in os.environ.get("SUDO_USERS", "").split())
    except ValueError:
        raise Exception(
            "Your dev or sudo users list does not contain valid integers.")

    try:
        SUPPORT_USERS = set(
            int(x) for x in os.environ.get("SUPPORT_USERS", "").split())
    except ValueError:
        raise Exception(
            "Your support users list does not contain valid integers.")

    try:
        WHITELIST_USERS = set(
            int(x) for x in os.environ.get("WHITELIST_USERS", "").split())
    except ValueError:
        raise Exception(
            "Your whitelisted users list does not contain valid integers.")

    try:
        IGNORE_PENDING_REQUESTS = int(
            os.environ.get('IGNORE_PENDING_REQUESTS', True))
    except KeyError:
        IGNORE_PENDING_REQUESTS = int(
            os.environ.get('IGNORE_PENDING_REQUESTS', False))

    WEBHOOK = bool(os.environ.get('WEBHOOK', False))
    URL = os.environ.get('URL', "")  # Does not contain token
    PORT = int(os.environ.get('PORT', 5000))
    CERT_PATH = os.environ.get("CERT_PATH")

    DB_URI = os.environ.get('DATABASE_URL')
    DB_NAME = os.environ.get('DB_NAME', None)
    LOAD = os.environ.get("LOAD", "").split()
    NO_LOAD = os.environ.get("NO_LOAD", "translation").split()
    DEL_CMDS = bool(os.environ.get('DEL_CMDS', False))
    STRICT_GBAN = bool(os.environ.get('STRICT_GBAN', False))
    STRICT_GMUTE = bool(os.environ.get('STRICT_GMUTE', False))
    WORKERS = int(os.environ.get('WORKERS', 8))
    BAN_STICKER = os.environ.get('BAN_STICKER',
                                 'CAADAgADOwADPPEcAXkko5EB3YGYAg')
    ALLOW_EXCL = os.environ.get('ALLOW_EXCL', False)
    SUPPORT_CHAT = os.environ.get('SUPPORT_CHAT', None)
    INFOPIC = bool(os.environ.get("INFOPIC", False))
    START_STICKER = os.environ.get(
        'START_STICKER',
        'CAACAgIAAx0CWFZqDQABBkpeYT4ykmRFN7qjtrzCH4-EYzGVkGwAAmIAA3_0Mxx8ZiETK_KDeiAE'
    )
    LOGS = os.environ.get('LOGS', None)
    BACKUP_PASS = os.environ.get("BACKUP_PASS", True)

else:
    from tg_bot.config import Development as Config
    TOKEN = Config.API_KEY
    try:
        OWNER_ID = int(Config.OWNER_ID)
    except ValueError:
        raise Exception("Your OWNER_ID variable is not a valid integer.")

    MESSAGE_DUMP = Config.MESSAGE_DUMP
    OWNER_USERNAME = Config.OWNER_USERNAME

    try:
        DEV_USERS = set(int(x) for x in Config.DEV_USERS or [])
        SUDO_USERS = set(int(x) for x in Config.SUDO_USERS or [])
    except ValueError:
        raise Exception(
            "Your dev or sudo users list does not contain valid integers.")

    try:
        SUPPORT_USERS = set(int(x) for x in Config.SUPPORT_USERS or [])
    except ValueError:
        raise Exception(
            "Your support users list does not contain valid integers.")

    try:
        WHITELIST_USERS = set(int(x) for x in Config.WHITELIST_USERS or [])
    except ValueError:
        raise Exception(
            "Your whitelisted users list does not contain valid integers.")

    WEBHOOK = Config.WEBHOOK
    URL = Config.URL
    PORT = Config.PORT
    CERT_PATH = Config.CERT_PATH

    DB_URI = Config.SQLALCHEMY_DATABASE_URI
    DB_NAME = Config.DB_NAME
    LOAD = Config.LOAD
    NO_LOAD = Config.NO_LOAD
    DEL_CMDS = Config.DEL_CMDS
    STRICT_GBAN = Config.STRICT_GBAN
    STRICT_GMUTE = Config.STRICT_GMUTE
    WORKERS = Config.WORKERS
    BAN_STICKER = Config.BAN_STICKER
    ALLOW_EXCL = Config.ALLOW_EXCL
    SUPPORT_CHAT = Config.SUPPORT_CHAT
    INFOPIC = Config.INFOPIC
    START_STICKER = Config.START_STICKER
    LOGS = Config.LOGS
    BACKUP_PASS = Config.BACKUP_PASS
    IGNORE_PENDING_REQUESTS = Config.IGNORE_PENDING_REQUESTS

DEV_USERS.add(OWNER_ID)
SUDO_USERS.add(OWNER_ID)

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
