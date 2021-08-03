"""
import os
from datetime import datetime
import yaml
from gtts import gTTS
from telegram import ChatAction, Update, ParseMode
from telegram.ext import CommandHandler, run_async

from tg_bot import dispatcher, CallbackContext


def tts(update: Update, context: CallbackContext):
    current_time = datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S")
    filename = datetime.now().strftime("%d%m%y-%H%M%S%f")
    update.message.chat.send_action(ChatAction.RECORD_AUDIO)
    reply = update.message.reply_to_message
    if reply is None:
        text = "".join(context.args)
    elif reply.text is not None:
        text = reply.text
    else:
        return
    if len(text) == 0:
        update.message.reply_text(
            "Reply a message or give something like:\n`/tts <message>`",
            parse_mode=ParseMode.MARKDOWN
            )
        return
    tts = gTTS(text)
    tts.save(filename + ".mp3")
    with open(filename + ".mp3", "rb") as speech:
        update.message.reply_voice(speech, quote=True)
    os.remove(filename + ".mp3")


TTS_HANDLER = CommandHandler("tts", tts, run_async=True)

dispatcher.add_handler(TTS_HANDLER)"""
