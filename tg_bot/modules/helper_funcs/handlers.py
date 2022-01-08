import telegram.ext as tg
from telegram import Update
from tg_bot import ALLOW_EXCL

if ALLOW_EXCL:
    CMD_STARTERS = ("/', '!")
else:
    CMD_STARTERS = ("/", )


class CustomCommandHandler(tg.CommandHandler):

    def __init__(self, command, callback, run_async=True, **kwargs):
        if "admin_ok" in kwargs:
            del kwargs["admin_ok"]
        super().__init__(command, callback, **kwargs)

        self.run_async = run_async

    def check_update(self, update):
        if isinstance(update, Update) and update.effective_message:
            message = update.effective_message
            try:
                user_id = update.effective_user.id
            except:
                user_id = None

            if message.text and len(message.text) > 1:
                fst_word = message.text.split(None, 1)[0]
                if len(fst_word) > 1 and any(
                        fst_word.startswith(start) for start in CMD_STARTERS):

                    args = message.text.split()[1:]
                    command = fst_word[1:].split("@")
                    command.append(message.bot.username)
                    if user_id == 1087968824:
                        user_id = update.effective_chat.id
                    if not (command[0].lower() in self.command
                            and command[1].lower()
                            == message.bot.username.lower()):
                        return None
                    filter_result = self.filters(update)
                    if filter_result:
                        return args, filter_result
                    else:
                        return False


class CustomRegexHandler(tg.MessageHandler):

    def __init__(self, pattern, callback, friendly="", **kwargs):
        super().__init__(tg.Filters.regex(pattern), callback, **kwargs)
