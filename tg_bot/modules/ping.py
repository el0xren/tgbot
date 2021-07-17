import time
from datetime import datetime

from telegram.ext import CommandHandler
from telegram.update import Update
from telegram import ParseMode

from tg_bot import dispatcher, CallbackContext


def ping(update: Update, context: CallbackContext):
    before = datetime.now()
    message = update.message.reply_text("Appraising..")
    now =  datetime.now()
    res = (now-before).microseconds / 1000
    update.message.bot.edit_message_text(f"<b>PONG!</b>\nTime taken: <code>{res}ms</code>", update.message.chat_id, message.message_id, parse_mode=ParseMode.HTML)


PING_HANDLER = CommandHandler("ping", ping, run_async=True)

dispatcher.add_handler(PING_HANDLER)
