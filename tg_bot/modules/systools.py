import requests
import re

from subprocess import Popen, PIPE

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, Filters
from telegram.ext.callbackqueryhandler import CallbackQueryHandler

from tg_bot import dispatcher, CallbackContext, OWNER_ID, SUDO_USERS


def shell(update: Update, context: CallbackContext):
    command = update.message.text.replace("/sh" or "/shell","").split(" ", 1)[1]
    msg = update.message.reply_text(f"~$ {command}")
    out = Popen(command,shell=True,stdout=PIPE,stderr=PIPE)
    stdout,stderr = out.communicate()
    output = str(stderr.decode() + stdout.decode())
    update.message.bot.edit_message_text(
        f"<b>~$ {command}</b>\n<code>{output}</code>",
        chat_id=update.message.chat_id,
        message_id=msg.message_id,
        parse_mode="HTML")


def logs(update: Update, context: CallbackContext):
    user = update.effective_user
    with open("log.txt", "rb") as f:
        context.bot.send_document(document=f, filename=f.name, chat_id=user.id)


def leave(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if args:
        chat_id = str(args[0])
        leave_msg = " ".join(args[1:])
        try:
            context.bot.send_message(chat_id, leave_msg)
            bot.leave_chat(int(chat_id))
            update.effective_message.reply_text("Left chat.")
        except TelegramError:
            update.effective_message.reply_text("Failed to leave chat for some reason.")
    else:
        chat = update.effective_chat
        kb = [[
            InlineKeyboardButton(text="I am sure of this action.", callback_data="leavechat_cb_({})".format(chat.id))
        ]]
        update.effective_message.reply_text("I'm going to leave {}, press the button below to confirm".format(chat.title), reply_markup=InlineKeyboardMarkup(kb))


def leave_cb(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    if callback.from_user.id not in SUDO_USERS:
        callback.answer(text="This isn't for you", show_alert=True)
        return

    match = re.match(r"leavechat_cb_\((.+?)\)", callback.data)
    chat = int(match.group(1))
    bot.leave_chat(chat_id=chat)
    callback.answer(text="Left chat")


def get_bot_ip(update: Update, context: CallbackContext):
    """ Sends the bot's IP address, so as to be able to ssh in if necessary.
        OWNER ONLY.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


SHELL_HANDLER = CommandHandler(["sh", "shell"], shell, filters=Filters.user(OWNER_ID), run_async=True)
LOG_HANDLER = CommandHandler("logs", logs, filters=Filters.user(OWNER_ID), run_async=True)
LEAVE_HANDLER = CommandHandler("leave", leave, run_async=True)
LEAVE_CALLBACK = CallbackQueryHandler(leave_cb, pattern=r"leavechat_cb_", run_async=True)
IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=Filters.user(OWNER_ID), run_async=True)

dispatcher.add_handler(SHELL_HANDLER)
dispatcher.add_handler(LOG_HANDLER)
dispatcher.add_handler(LEAVE_HANDLER)
dispatcher.add_handler(LEAVE_CALLBACK)
dispatcher.add_handler(IP_HANDLER)
