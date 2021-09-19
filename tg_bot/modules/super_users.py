import html

from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, CallbackContext, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS
from tg_bot.modules.helper_funcs.chat_status import sudo_plus, support_plus, whitelist_plus


@whitelist_plus
def whitelistlist(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    msg = "ㅤ<b>Whitelist users:</b>\n"
    for each_user in WHITELIST_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            msg += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    message.reply_text(msg, parse_mode=ParseMode.HTML)


@whitelist_plus
def supportlist(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    msg = "ㅤ<b>Support users:</b>\n"
    for each_user in SUPPORT_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            msg += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    message.reply_text(msg, parse_mode=ParseMode.HTML)


@whitelist_plus
def sudolist(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    true_sudo = list(set(SUDO_USERS))
    msg = "ㅤ<b>Sudo users:</b>\n"
    for each_user in true_sudo:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            msg += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    message.reply_text(msg, parse_mode=ParseMode.HTML)


__help__ = """
- /sudolist lists all users which have sudo access to the bot
- /supportlist lists all users which are allowed to gban, but can also be banned
- /whitelistlist lists all users which cannot be banned, muted flood or kicked but can be manually banned by admins
"""

__mod_name__ = "Super Users"

SUDOLIST_HANDLER = CommandHandler(("sudolist"), sudolist, run_async=True)
SUPPORTLIST_HANDLER = CommandHandler(("supportlist"), supportlist, run_async=True)
WHITELISTLIST_HANDLER = CommandHandler(("whitelistlist"), whitelistlist, run_async=True)

dispatcher.add_handler(SUDOLIST_HANDLER)
dispatcher.add_handler(SUPPORTLIST_HANDLER)
dispatcher.add_handler(WHITELISTLIST_HANDLER)
