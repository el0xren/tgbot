import datetime
import importlib
import re
import logging
import traceback
import html
import json
import sys
import time
from typing import Optional, List
from io import BytesIO

from telegram import Message, Chat, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import CommandHandler, Filters, MessageHandler, CallbackQueryHandler
from telegram.ext.dispatcher import run_async, DispatcherHandlerStop, Dispatcher
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher, updater, CallbackContext, TOKEN, WEBHOOK, OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS, CERT_PATH, PORT, URL, LOGGER, \
    ALLOW_EXCL, SUPPORT_CHAT, START_STICKER, IGNORE_PENDING_REQUESTS
from tg_bot.modules import ALL_MODULES
from tg_bot.modules.helper_funcs.chat_status import is_user_admin
from tg_bot.modules.helper_funcs.misc import paginate_modules
from tg_bot.modules.helper_funcs.misc import send_to_list

BOT_IMG = "https://telegra.ph/file/572f1989b04f0eefa53b0.jpg"

PM_START_TEXT = """
Hi {}, my name is {}!
I'm a group manager bot built in python3, using the python-telegram-bot library.

I'll help you manage your groups in an efficient way!

You can find the list of available commands with /help.
"""

HELP_STRINGS = """
Hey there! My name is *{}*.
I'm a modular group management bot with a few fun extras! Have a look at the following for an idea of some of \
the things I can help you with.

*Main* available commands:
 - /start: start the bot
 - /help: PM's you this message.
 - /help <module name>: PM's you info about that module.
 - /settings:
   - in PM: will send you your settings for all supported modules.
   - in a group: will redirect you to pm, with all that chat's settings.

{}
And the following:
""".format(
    dispatcher.bot.first_name, ""
    if not ALLOW_EXCL else "\nAll commands can either be used with / or !.\n")

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []

CHAT_SETTINGS = {}
USER_SETTINGS = {}

GDPR = []

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("tg_bot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if not imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception(
            "Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__gdpr__"):
        GDPR.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(chat_id=chat_id,
                                text=text,
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=keyboard)


def start(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id,
                                  False)
                else:
                    send_settings(match.group(1), update.effective_user.id,
                                  True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            update.effective_message.reply_document(START_STICKER)
            update.effective_message.reply_text(
                PM_START_TEXT.format(escape_markdown(first_name),
                                     escape_markdown(bot.first_name),
                                     OWNER_ID),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton(text="Source Code",
                                             url="github.com/el0xren/tgbot")
                    ],
                     [
                         InlineKeyboardButton(text="Support Group",
                                              url=f"t.me/{SUPPORT_CHAT}")
                     ],
                     [
                         InlineKeyboardButton(
                             text="Add {} to your group".format(
                                 dispatcher.bot.first_name),
                             url="t.me/{}?startgroup=true".format(
                                 context.bot.username))
                     ]]))
    else:
        update.effective_message.reply_text("Yo, whadup?")


def error_callback(update: Update, context: CallbackContext):
    LOGGER.error("Exception while handling an update:", exc_info=context.error)

    # Prepare traceback and context info
    try:
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)

        update_str = {}
        if isinstance(update, Update):
            update_dict = update.to_dict()
            message = update_dict.get("message", {})
            update_str = {
                "update_id": update_dict.get("update_id"),
                "chat": {
                    "id": message.get("chat", {}).get("id"),
                    "type": message.get("chat", {}).get("type"),
                    "username": message.get("chat", {}).get("username"),
                    "title": message.get("chat", {}).get("title")
                } if message.get("chat") else None,
                "from": {
                    "id": message.get("from", {}).get("id"),
                    "first_name": message.get("from", {}).get("first_name"),
                    "username": message.get("from", {}).get("username")
                } if message.get("from") else None,
                "text": message.get("text"),
                "entities": message.get("entities")
            }

        # Summary for message
        summary = (
            f"<b>Error:</b> {str(context.error)}\n"
            f"<b>Severity:</b> Critical\n"
            f"<b>Timestamp:</b> {datetime.datetime.now(datetime.UTC).isoformat()}\n"
            f"<b>Bot:</b> @{context.bot.username}\n"
            f"<b>Python:</b> {sys.version.split()[0]}\n"
            f"📎 See attached file for full traceback."
        )

        # Full document
        full_message = (
            f"Error: {str(context.error)}\n"
            f"Severity: Critical\n"
            f"Timestamp: {datetime.datetime.now(datetime.UTC).isoformat()}\n"
            f"Bot: @{context.bot.username}\n"
            f"Python: {sys.version.split()[0]}\n\n"
            f"Update:\n{json.dumps(update_str, indent=2, ensure_ascii=False)}\n\n"
            f"Chat Data:\n{context.chat_data}\n\n"
            f"User Data:\n{context.user_data}\n\n"
            f"Traceback:\n{tb_string}"
        )

    except Exception as e:
        LOGGER.error(f"Failed to generate traceback message: {e}", exc_info=True)
        summary = f"Error: {str(context.error)}\n(Failed to format traceback due to: {str(e)})"
        full_message = summary

    file = BytesIO(full_message.encode('utf-8'))
    file.name = f"traceback_{int(time.time())}.txt"
    file.seek(0)

    recipients = set()
    if isinstance(OWNER_ID, int):
        recipients.add(OWNER_ID)
    if DEV_USERS:
        recipients.update(uid for uid in DEV_USERS if isinstance(uid, int))

    for user_id in recipients:
        try:
            context.bot.send_message(chat_id=user_id, text=summary, parse_mode=ParseMode.HTML)
            file.seek(0)
            context.bot.send_document(chat_id=user_id, document=file)
            LOGGER.info(f"Traceback sent to {user_id}")
        except TelegramError as e:
            LOGGER.warning(f"Failed to send to {user_id}: {e}")


def help_button(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)
    try:
        if mod_match:
            module = mod_match.group(1)
            text = "Here is the help for the *{}* module:\n".format(HELPABLE[module].__mod_name__) \
                   + HELPABLE[module].__help__
            query.message.edit_text(text=text,
                                    parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=InlineKeyboardMarkup([[
                                        InlineKeyboardButton(
                                            text="Back",
                                            callback_data="help_back")
                                    ]]))

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(HELP_STRINGS,
                                    parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=InlineKeyboardMarkup(
                                        paginate_modules(
                                            curr_page - 1, HELPABLE, "help")))

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(HELP_STRINGS,
                                    parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=InlineKeyboardMarkup(
                                        paginate_modules(
                                            next_page + 1, HELPABLE, "help")))

        elif back_match:
            query.message.edit_text(text=HELP_STRINGS,
                                    parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=InlineKeyboardMarkup(
                                        paginate_modules(0, HELPABLE, "help")))

        bot.answer_callback_query(query.id)
    except BadRequest as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            LOGGER.exception("Exception in help buttons. %s", str(query.data))


def get_help(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    args = update.effective_message.text.split(None, 1)

    if chat.type != chat.PRIVATE:
        update.effective_message.reply_text(
            "Contact me in PM to get the list of possible commands.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(text="Help",
                                     url="t.me/{}?start=help".format(
                                         bot.username))
            ]]))
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = "Here is the available help for the *{}* module:\n".format(HELPABLE[module].__mod_name__) \
               + HELPABLE[module].__help__
        send_help(
            chat.id, text,
            InlineKeyboardMarkup([[
                InlineKeyboardButton(text="Back", callback_data="help_back")
            ]]))

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join("*{}*:\n{}".format(
                mod.__mod_name__, mod.__user_settings__(user_id))
                                   for mod in USER_SETTINGS.values())
            dispatcher.bot.send_message(user_id,
                                        "These are your current settings:" +
                                        "\n\n" + settings,
                                        parse_mode=ParseMode.MARKDOWN)

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN)

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".
                format(chat_name),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)))
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN)


def settings_button(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(escape_markdown(chat.title),
                                                                                     CHAT_SETTINGS[
                                                                                         module].__mod_name__) + \
                   CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text="Back",
                        callback_data="stngs_back({})".format(chat_id))
                ]]))

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.edit_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1,
                                     CHAT_SETTINGS,
                                     "stngs",
                                     chat=chat_id)))

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.edit_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1,
                                     CHAT_SETTINGS,
                                     "stngs",
                                     chat=chat_id)))

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.edit_text(
                text=
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)))

        bot.answer_callback_query(query.id)
    except BadRequest as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            LOGGER.exception("Exception in settings buttons. %s",
                             str(query.data))


def get_settings(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = msg.text.split(None, 1)

    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(text,
                           reply_markup=InlineKeyboardMarkup([[
                               InlineKeyboardButton(
                                   text="Settings",
                                   url="t.me/{}?start=stngs_{}".format(
                                       bot.username, chat.id))
                           ]]))
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)


def migrate_chats(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def test_error(update: Update, context: CallbackContext):
    raise Exception("This is a test error!")


def get_chat_id(update: Update, context: CallbackContext):
    update.effective_message.reply_text(f"Chat ID: {update.effective_chat.id}")


def debug_config(update: Update, context: CallbackContext):
    support_chat_status = SUPPORT_CHAT if SUPPORT_CHAT else "Not set"
    owner_id_status = OWNER_ID if OWNER_ID else "Not set"
    support_chat_id = None

    if SUPPORT_CHAT:
        if isinstance(SUPPORT_CHAT, str):
            chat_id_input = f"@{SUPPORT_CHAT}" if not SUPPORT_CHAT.startswith('@') else SUPPORT_CHAT
            try:
                chat = context.bot.get_chat(chat_id_input)
                support_chat_id = chat.id
                support_chat_status = f"{chat_id_input} (resolved to {support_chat_id})"
            except TelegramError as e:
                support_chat_status = f"{chat_id_input} (failed to resolve: {e})"
        elif isinstance(SUPPORT_CHAT, int):
            support_chat_id = SUPPORT_CHAT
            support_chat_status = f"{SUPPORT_CHAT} (numeric ID)"

    support_chat_test = "Not tested"
    if support_chat_id:
        try:
            context.bot.send_message(chat_id=support_chat_id, text="Test message from debug_config")
            support_chat_test = "Message sent successfully"
        except TelegramError as e:
            support_chat_test = f"Failed to send message: {e}"

    owner_id_test = "Not tested"
    if OWNER_ID:
        try:
            context.bot.send_message(chat_id=OWNER_ID, text="Test message from debug_config")
            owner_id_test = "Message sent successfully"
        except TelegramError as e:
            owner_id_test = f"Failed to send message: {e}"

    update.effective_message.reply_text(
        f"Debug Configuration:\n"
        f"SUPPORT_CHAT: {support_chat_status}\n"
        f"SUPPORT_CHAT Test: {support_chat_test}\n"
        f"OWNER_ID: {owner_id_status}\n"
        f"OWNER_ID Test: {owner_id_test}"
    )


def main():
    start_handler = CommandHandler("start", start, run_async=True)
    help_handler = CommandHandler("help", get_help, run_async=True)
    help_callback_handler = CallbackQueryHandler(help_button,
                                                 pattern=r"help_",
                                                 run_async=True)
    settings_handler = CommandHandler("settings", get_settings, run_async=True)
    settings_callback_handler = CallbackQueryHandler(settings_button,
                                                     pattern=r"stngs_",
                                                     run_async=True)
    migrate_handler = MessageHandler(Filters.status_update.migrate,
                                     migrate_chats)
    test_error_handler = CommandHandler("testerror", test_error, run_async=True)
    chat_id_handler = CommandHandler("chatid", get_chat_id, run_async=True)
    debug_config_handler = CommandHandler("debugconfig", debug_config, run_async=True)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(test_error_handler)
    dispatcher.add_handler(chat_id_handler)
    dispatcher.add_handler(debug_config_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN,
                                    certificate=open(CERT_PATH, 'rb'))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        if SUPPORT_CHAT:
            try:
                dispatcher.bot.sendMessage(f"@{SUPPORT_CHAT}", "I'm awake now!")
            except TelegramError:
                send_to_list(dispatcher.bot, DEV_USERS + SUDO_USERS,
                             "I'm awake now!")
        else:
            send_to_list(dispatcher.bot, DEV_USERS + SUDO_USERS,
                         "I'm awake now!")
        LOGGER.info(f"Configuration: SUPPORT_CHAT={SUPPORT_CHAT}, OWNER_ID={OWNER_ID}")
        LOGGER.info(f"Bot username: @{dispatcher.bot.username}")
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15,
                              read_latency=4,
                              drop_pending_updates=IGNORE_PENDING_REQUESTS)

    updater.idle()


CHATS_CNT = {}
CHATS_TIME = {}

if __name__ == '__main__':
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    main()
