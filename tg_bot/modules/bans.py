import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User, ParseMode
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, CallbackContext, BAN_STICKER, LOGGER, SUDO_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, can_delete
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable


@bot_admin
@can_restrict
@user_admin
@loggable
def ban(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    sender_id = update.effective_user.id

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    if user_id == sender_id:
        message.reply_text("You cannot ban yourself.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_ban_protected(update, user_id, member):
        message.reply_text("I really wish I could ban admins...")
        return ""

    if user_id == bot.id:
        message.reply_text("I cannot ban myself.")
        return ""

    if message.text.startswith("/d") and message.reply_to_message:
        message.reply_to_message.delete()

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.ban_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)
        message.reply_text(
            "Banned!\n<b>ID:</b> <code>{}</code>".format(user_id),
            parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Banned!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Well damn, I can't ban that user.")

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    sender_id = update.effective_user.id

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    if user_id == sender_id:
        message.reply_text("You cannot ban yourself.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_ban_protected(update, user_id, member):
        message.reply_text("I really wish I could ban admins...")
        return ""

    if user_id == bot.id:
        message.reply_text("I cannot ban myself.")
        return ""

    if not reason:
        message.reply_text(
            "You haven't specified a time to ban this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name),
                                     member.user.id,
                                     time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.ban_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)
        message.reply_text(
            "Banned! User will be banned for {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                "Banned! User will be banned for {}.".format(time_val),
                quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Well damn, I can't ban that user.")

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
def kick(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    sender_id = update.effective_user.id

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    if user_id == sender_id:
        message.reply_text("You cannot ban yourself.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_ban_protected(update, user_id):
        message.reply_text("I really wish I could kick admins...")
        return ""

    if user_id == bot.id:
        message.reply_text("I cannot ban myself.")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        if message.text.startswith("/s"):
            silent = True
            if not can_delete(chat, context.bot.id):
                return ""
        else:
            silent = False

        if silent:
            if message.reply_to_message:
                message.reply_to_message.delete()
            message.delete()

        else:
            bot.send_sticker(chat.id, BAN_STICKER)
            message.reply_text("Kicked!")
            log = "<b>{}:</b>" \
                  "\n#KICKED" \
                  "\n<b>Admin:</b> {}" \
                  "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                               mention_html(user.id, user.first_name),
                                                               mention_html(member.user.id, member.user.first_name),
                                                               member.user.id)
            if reason:
                log += "\n<b>Reason:</b> {}".format(reason)

            return log

    else:
        message.reply_text("Well damn, I can't kick that user.")

    return ""


@bot_admin
@can_restrict
def kickme(update: Update, context: CallbackContext):
    bot = context.bot
    user_id = update.effective_message.from_user.id
    if is_user_admin(update, user_id):
        update.effective_message.reply_text(
            "I wish I could... but you're an admin.")
        return

    res = update.effective_chat.unban_member(
        user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("No problem.")
    else:
        update.effective_message.reply_text("Huh? I can't.")


@bot_admin
@can_restrict
def banme(update: Update, context: CallbackContext):
    bot = context.bot
    user_id = update.effective_message.from_user.id
    chat = update.effective_chat
    user = update.effective_user
    if is_user_admin(update, user_id):
        update.effective_message.reply_text(
            "I wish I could... but you're an admin.")
        return

    res = update.effective_chat.ban_member(user_id)
    if res:
        update.effective_message.reply_text("No problem.")
    else:
        update.effective_message.reply_text("Huh? I can't.")


@bot_admin
@can_restrict
@user_admin
@loggable
def sban(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    update.effective_message.delete()

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            return ""
        else:
            raise

    if is_user_ban_protected(update, user_id, member):
        return ""

    if user_id == bot.id:
        return ""

    log = "<b>{}:</b>" \
          "\n#SILENTBAN" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}".format(html.escape(chat.title),
                                    mention_html(user.id, user.first_name),
                                    mention_html(member.user.id, member.user.first_name),
                                    member.user.id)
    if reason:
        log += "\n<b>• Reason:</b> {}".format(reason)

    try:
        chat.ban_member(user_id)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
def unban(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    sender_id = update.effective_user.id

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    if user_id == sender_id:
        message.reply_text("You cannot unban yourself.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("I cannot unban myself.")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text(
            "Why are you trying to unban someone that's already in the chat?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("Yep, this user can join!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    return log


__help__ = """
 - /banme: bans the user who issues the command
 - /kickme: kicks the user who issued the command

*Admin only:*
 - /sban <userhandle>: silently bans a user. (via handle, or reply)
 - /dban <userhandle>: bans a user and deletes the message which is replied to.
 - /ban <userhandle>: bans a user. (via handle, or reply)
 - /tban <userhandle> x(m/h/d): bans a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
 - /unban <userhandle>: unbans a user. (via handle, or reply)
 - /kick <userhandle>: kicks a user, (via handle, or reply)
 - /skick <userhandle>: silently kicks a user. (via handle, or reply)
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler(["ban", "dban"],
                             ban,
                             filters=Filters.chat_type.groups,
                             run_async=True)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"],
                                 temp_ban,
                                 filters=Filters.chat_type.groups,
                                 run_async=True)
KICK_HANDLER = CommandHandler(["kick", "skick"],
                              kick,
                              filters=Filters.chat_type.groups,
                              run_async=True)
UNBAN_HANDLER = CommandHandler("unban",
                               unban,
                               filters=Filters.chat_type.groups,
                               run_async=True)
KICKME_HANDLER = DisableAbleCommandHandler("kickme",
                                           kickme,
                                           filters=Filters.chat_type.groups,
                                           run_async=True)
BANME_HANDLER = DisableAbleCommandHandler("banme",
                                          banme,
                                          filters=Filters.chat_type.groups,
                                          run_async=True)
SBAN_HANDLER = CommandHandler("sban",
                              sban,
                              filters=Filters.chat_type.groups,
                              run_async=True)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(BANME_HANDLER)
dispatcher.add_handler(SBAN_HANDLER)
