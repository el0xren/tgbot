from subprocess import Popen, PIPE

from telegram import Update
from telegram.ext import CommandHandler, Filters

from tg_bot import dispatcher, CallbackContext, OWNER_ID


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


SHELL_HANDLER = CommandHandler(["sh", "shell"], shell, filters=Filters.user(OWNER_ID), run_async=True)

dispatcher.add_handler(SHELL_HANDLER)