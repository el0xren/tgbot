import requests
import re
import time

from datetime import datetime
from subprocess import Popen, PIPE
from speedtest import Speedtest

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, TelegramError
from telegram.ext import CommandHandler, Filters
from telegram.ext.callbackqueryhandler import CallbackQueryHandler

from tg_bot import dispatcher, CallbackContext, OWNER_ID, DEV_USERS, SUDO_USERS
from tg_bot.modules.sql.systools_sql import last_speedtest
from tg_bot.modules.helper_funcs.chat_status import owner_plus, dev_plus, sudo_plus


@owner_plus
def shell(update: Update, context: CallbackContext):
    command = update.message.text.split(' ', 1)
    if len(command) == 1:
        update.message.reply_text('No command to execute was given.')
        return
    command = command[1]
    msg = update.message.reply_text(f"~$ {command}")
    out = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = out.communicate()
    
    import html
    output = html.escape(stderr.decode() + stdout.decode())
    
    update.message.bot.edit_message_text(
        f"<b>~$ {command}</b>\n<code>{output}</code>",
        chat_id=update.message.chat_id,
        message_id=msg.message_id,
        parse_mode="HTML")


@dev_plus
def logs(update: Update, context: CallbackContext):
    user = update.effective_user
    with open("log.txt", "rb") as f:
        context.bot.send_document(document=f, filename=f.name, chat_id=user.id)


@dev_plus
def leave(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if args:
        chat_id = str(args[0])
        leave_msg = " ".join(args[1:])
        try:
            bot.leave_chat(int(chat_id))
            update.effective_message.reply_text("Left chat.")
        except TelegramError:
            update.effective_message.reply_text(
                "Failed to leave chat for some reason.")
    else:
        chat = update.effective_chat
        kb = [[
            InlineKeyboardButton(text="I am sure of this action.",
                                 callback_data="leavechat_cb_({})".format(
                                     chat.id))
        ]]
        update.effective_message.reply_text(
            "I'm going to leave {}, press the button below to confirm".format(
                chat.title),
            reply_markup=InlineKeyboardMarkup(kb))


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


@owner_plus
def get_bot_ip(update: Update, context: CallbackContext):
    """ Sends the bot's IP address, so as to be able to ssh in if necessary.
        OWNER ONLY.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


@sudo_plus
def ping(update: Update, context: CallbackContext):
    message = update.effective_message
    user = update.effective_user

    if user.id != OWNER_ID and user.id not in DEV_USERS and user.id not in SUDO_USERS:
        return message.reply_text("Ping Pong... Your opinion is wrong.")

    before = datetime.now()
    message = update.message.reply_text("Pinging..")
    now = datetime.now()
    res = (now - before).microseconds / 1000
    update.message.bot.edit_message_text(
        f"<b>PONG!</b>\nTime taken: <code>{res}ms</code>",
        update.message.chat_id,
        message.message_id,
        parse_mode=ParseMode.HTML)


@dev_plus
def speedtest(update: Update, context: CallbackContext):
    now = datetime.now()
    if last_speedtest.date is not None and (
            now - last_speedtest.date).seconds < 5 * 60:
        update.message.reply_text(
            f"<b>Download:</b> <code>{last_speedtest.download}</code> mbps\n"
            f"<b>Upload:</b> <code>{last_speedtest.upload}</code> mbps\n\n"
            f"Cached results from {last_speedtest.date.strftime('<code>%m/%d/%Y</code>, <code>%H:%M:%S</code>')}",
            parse_mode=ParseMode.HTML)
        return
    message_id = update.message.reply_text(
        "<code>Running speedtest...</code>",
        parse_mode=ParseMode.HTML).message_id
    speedtest = Speedtest()
    speedtest.get_best_server()
    speedtest.download()
    speedtest.upload()
    speedtest.results.share()
    results_dict = speedtest.results.dict()
    download = str(results_dict["download"] // 10**6)
    upload = str(results_dict["upload"] // 10**6)
    last_speedtest.set_data(now, download, upload)
    context.bot.edit_message_text(
        chat_id=update.message.chat_id,
        message_id=message_id,
        text=f"<b>Download:</b> <code>{download}</code> mbps\n"
        f"<b>Upload:</b> <code>{upload}</code> mbps",
        parse_mode=ParseMode.HTML)


SHELL_HANDLER = CommandHandler(["sh", "shell"], shell, run_async=True)
LOG_HANDLER = CommandHandler("logs", logs, run_async=True)
LEAVE_HANDLER = CommandHandler("leave", leave, run_async=True)
LEAVE_CALLBACK = CallbackQueryHandler(leave_cb,
                                      pattern=r"leavechat_cb_",
                                      run_async=True)
IP_HANDLER = CommandHandler("ip", get_bot_ip, run_async=True)
PING_HANDLER = CommandHandler("ping", ping, run_async=True)
SPEEDTEST_HANDLER = CommandHandler("speedtest", speedtest, run_async=True)

dispatcher.add_handler(SHELL_HANDLER)
dispatcher.add_handler(LOG_HANDLER)
dispatcher.add_handler(LEAVE_HANDLER)
dispatcher.add_handler(LEAVE_CALLBACK)
dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(SPEEDTEST_HANDLER)
