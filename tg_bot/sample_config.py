# Create a new config.py or rename this to config.py file in same dir and import, then extend this class.
import json
import os


def get_user_list(config, key):
    with open('{}/tg_bot/{}'.format(os.getcwd(), config), 'r') as json_file:
        return json.load(json_file)[key]


# Create a new config.py file in same dir and import, then extend this class.
class Config(object):
    LOGGER = True

    # REQUIRED
    API_KEY = "YOUR KEY HERE"
    OWNER_ID = "YOUR ID HERE"  # If you dont know, run the bot and do /id in your private chat with it
    OWNER_USERNAME = "YOUR USERNAME HERE"

    # RECOMMENDED
    SQLALCHEMY_DATABASE_URI = 'sqldbtype://username:pw@hostname:port/db_name'  # needed for any database modules
    DB_NAME = "databasename"  # needed for cron_jobs module, use same databasename from SQLALCHEMY_DATABASE_URI
    MESSAGE_DUMP = None  # needed to make sure 'save from' messages persist
    LOAD = []
    # sed has been disabled after the discovery that certain long-running sed commands maxed out cpu usage
    # and killed the bot. Be careful re-enabling it!
    NO_LOAD = []
    WEBHOOK = False
    URL = None

    # OPTIONAL
    DEV_USERS = get_user_list("elevated_users.json", "devs") # List of id's - (not usernames) for developers who will have almost full control of the bot.
    SUDO_USERS = get_user_list("elevated_users.json", "sudos")  # List of id's (not usernames) for users which have sudo access to the bot.
    SUPPORT_USERS = get_user_list("elevated_users.json", "supports")  # List of id's (not usernames) for users which are allowed to gban, but can also be banned.
    WHITELIST_USERS = get_user_list("elevated_users.json", "whitelists")  # List of id's (not usernames) for users which WONT be banned/kicked by the bot.
    CERT_PATH = None
    PORT = 5000
    DEL_CMDS = False  # Whether or not you should delete "blue text must click" commands
    STRICT_GBAN = False
    STRICT_GMUTE = False
    WORKERS = 8  # Number of subthreads to use. This is the recommended amount - see for yourself what works best!
    BAN_STICKER = 'CAADAgADOwADPPEcAXkko5EB3YGYAg'  # banhammer marie sticker
    ALLOW_EXCL = False  # Allow ! commands as well as /
    SUPPORT_CHAT = None # Chat username without @
    INFOPIC = False
    START_STICKER = 'CAACAgIAAx0CWFZqDQABBkpeYT4ykmRFN7qjtrzCH4-EYzGVkGwAAmIAA3_0Mxx8ZiETK_KDeiAE'
    LOGS = None
    BACKUP_PASS = "12345" # The password used for the cron backups zip
    IGNORE_PENDING_REQUESTS = False


class Production(Config):
    LOGGER = False


class Development(Config):
    LOGGER = True
