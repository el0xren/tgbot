img align="right" width="260" height="260" alt="MissAhegaoBot" src="https://i.ibb.co/QfBPjQL/Avatars-Xyju6-Oujg-Jzzrbp9-bg6-Ny-A-t500x500.jpg">

# **MissAhegaoBot**
> *"She bans. She slaps. She runs on Python. She's single."*

The most unnecessarily modular Telegram bot in the wild.  
Built with **Python 3**, backed by **PostgreSQL**, and overflowing with chaos.

---

[![Use me](https://img.shields.io/badge/Use-On%20Telegram-FF69B4?logo=telegram)](https://t.me/MissAhegaoBot)
[![Cry for help](https://img.shields.io/badge/Cry-For%20Support-179cde?logo=telegram)](https://t.me/MissAhegaoSupport)
[![Fresh drama](https://img.shields.io/badge/Latest-Updates-26A5E4?logo=telegram)](https://t.me/MissAhegaoNews)
[![Pythonic](https://img.shields.io/badge/We%20speak-Python%203.6+-blue?logo=python)](https://www.python.org)
[![RDBMS Cult](https://img.shields.io/badge/DB-PostgreSQL-336791?logo=postgresql)](https://www.postgresql.org)

> **Warning:** If you fork this and it breaks, I’ll send thoughts and prayers. No tech support for your Frankenstein builds.

---

## Why tho?

- **Modular AF** — Drop in a plugin, the bot eats it. No burps.
- **PostgreSQL-backed** — Because real bots don’t use flat files.
- **Drag-and-drop plugins** — Like Minecraft mods, but nerdier.
- **Group management** — Slap users, welcome new ones, filter memes.
- **Admin hierarchy** — Owner > Sudo > Peasant.

---

## Summon the Bot Locally (aka "Running it")

1. Clone it like your ex’s Spotify password:

```bash
git clone https://github.com/yourusername/MissAhegaoBot.git
cd MissAhegaoBot
```

2. Install dependencies like it’s 2012:

```bash
pip3 install -r requirements.txt
```

3. Yeet your config:

Inside `tg_bot/`, create `config.py`:

```python
from tg_bot.sample_config import Config

class Development(Config):
    OWNER_ID = 123456789  # put your ID, not your crush's
    API_KEY = "put-your-token-here"  # you did use BotFather, right?
    SQLALCHEMY_DATABASE_URI = "postgresql://user:pass@localhost:5432/db"
    SUDO_USERS = [111, 222]  # The chosen ones
    LOAD = []
    NO_LOAD = ['translation']  # Because we don't speak French
```

4. Send it:

```bash
python3 -m tg_bot
```

---

## PostgreSQL Setup (aka “Sacrificing a Goat”)

```bash
sudo apt install postgresql
sudo su - postgres
createuser -P -s YOUR_USER
createdb -O YOUR_USER YOUR_DB_NAME
```

Then your connection string looks like:

```
postgresql://user:password@localhost:5432/yourdbname
```

No spaces. No typos. No crying.

---

## Plugin Magic

Drop `.py` files in `modules/`.  
They auto-load. Like a microwave but for bot commands.

Example:

```python
from tg_bot import dispatcher

__mod_name__ = "Anime"
__help__ = "Use /baka to feel pain."

dispatcher.add_handler(...)
```

Also valid:

- `__stats__()` — for `/stats`
- `__migrate__()` — for group ID switches (Telegram moment)

---

## Config via ENV (for the cloud nerds)

Env variable mode supports:

- `TOKEN`, `OWNER_ID`, `DATABASE_URL`, `WEBHOOK`, etc.
- `LOAD`, `NO_LOAD`, `SUDO_USERS`, `SUPPORT_USERS`
- Even `BAN_STICKER`, because banning with style matters.

---

## Pro Gamer Tips

- Use Python 3.6+ or feel the wrath of unordered dicts.
- 8 threads is default. 9000 is excessive. Don’t be that guy.
- `/help` command auto-pulls from your module docs. Stop being lazy.

---

## Credits

- Inspired by [PaulSonOfLars](https://github.com/PaulSonOfLars)
- Maintained by **you**. Yes, YOU. Because I won’t help.
- If it works, you’re welcome. If it doesn’t, read the logs.

---

## Donate?

Sure. Put this in your config and manifest capitalism:

```env
DONATION_LINK=https://ko-fi.com/yourpage
```

---

## License

MIT.  
Do whatever you want. Just don’t DM me asking why your fork is on fire.

---

## How to Setup (aka “Pact with the Bot Goddess”)

Once you've installed the dependencies, you’ll need to summon the configuration ritual.

This bot uses a **`config.ini`** file instead of boring old Python configs. Here’s how to feed her soul:

### 1. Create a file called `config.ini` in your root directory:

```ini
[ahegaoconfig]
TOKEN = 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11  ; from @BotFather
OWNER_ID = 123456789                               ; your Telegram ID
OWNER_USERNAME = yourusername                      ; no @, just vibes
SQLALCHEMY_DATABASE_URI = postgresql://user:pass@localhost:5432/db
DB_NAME = missabot_db
MESSAGE_DUMP = -1001527488593

LOAD =
NO_LOAD = 
WEBHOOK = False
URL = 
PORT = 5000

DEV_USERS =
SUDO_USERS =
SUPPORT_USERS =
WHITELIST_USERS =

CERT_PATH = 
INFOPIC = False
DEL_CMDS = True
STRICT_GBAN = True
STRICT_GMUTE = False
WORKERS = 8
BAN_STICKER = CAADAgADOwADPPEcAXkko5EB3YGYAg
ALLOW_EXCL = True
SUPPORT_CHAT = missahegaosupport
START_STICKER = CAACAgIAAx0CWFZqDQABBkpeYT4ykmRFN7qjtrzCH4-EYzGVkGwAAmIAA3_0Mxx8ZiETK_KDeiAE
LOGS = 
BACKUP_PASS = 12345
IGNORE_PENDING_REQUESTS = True
```

> Pro Tip: If you're on Heroku or somewhere cloudy, these can also be set as environment variables. But let's be honest — `.ini` is prettier.

### 2. Loading the config in Python

Make your bot read this using `configparser`:

```python
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

TOKEN = config["ahegaoconfig"]["TOKEN"]
OWNER_ID = int(config["ahegaoconfig"]["OWNER_ID"])
```

Boom. Config done. You’re basically a sysadmin now.
