import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User, ChatPermissions, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, CallbackContext, LOGGER
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_admin, can_restrict
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable


@bot_admin
@user_admin
@loggable
def mute(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    sender_id = update.effective_user.id

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    if user_id == sender_id:
        message.reply_text("No. You're not going to mute yourself.")
        return ""

    if user_id == bot.id:
        message.reply_text("I'm not muting myself!")
        return ""

    member = chat.get_member(int(user_id))

    if member:
        if is_user_admin(update, user_id, member=member):
            message.reply_text("Afraid I can't stop an admin from talking!")

        elif member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(
                chat.id,
                user_id,
                permissions=ChatPermissions(can_send_messages=False))
            message.reply_text("Muted!")
            return "<b>{}:</b>" \
                   "\n#MUTE" \
                   "\n<b>Admin:</b> {}" \
                   "\n<b>User:</b> {}".format(html.escape(chat.title),
                                              mention_html(user.id, user.first_name),
                                              mention_html(member.user.id, member.user.first_name))

        else:
            message.reply_text("This user is already muted!")
    else:
        message.reply_text("This user isn't in the chat!")

    return ""


@bot_admin
@user_admin
@loggable
def unmute(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user. Use @username or reply to their message.", parse_mode=ParseMode.HTML)
        return ""

    if user_id == bot.id:
        message.reply_text("I'm not muting myself!", parse_mode=ParseMode.HTML)
        return ""

    if user_id == user.id:
        message.reply_text("You cannot unmute yourself!", parse_mode=ParseMode.HTML)
        return ""

    try:
        member = chat.get_member(int(user_id))
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("This user isn't in the chat!", parse_mode=ParseMode.HTML)
            return ""
        else:
            LOGGER.exception(f"Error fetching member {user_id} in chat {chat.id}: {excp.message}")
            message.reply_text(f"Error fetching user: {excp.message}", parse_mode=ParseMode.HTML)
            return ""

    if is_user_admin(update, user_id, member=member):
        message.reply_text("This user is an administrator and cannot be unmuted.", parse_mode=ParseMode.HTML)
        return ""

    if member.status in ('kicked', 'left'):
        message.reply_text("This user isn't in the chat, unmuting them won't make them talk!", parse_mode=ParseMode.HTML)
        return ""

    if (member.can_send_messages and member.can_send_media_messages and 
        member.can_send_other_messages and member.can_send_polls and 
        member.can_add_web_page_previews):
        message.reply_text("This user already has the right to speak.", parse_mode=ParseMode.HTML)
        return ""

    try:
        bot.restrict_chat_member(
            chat.id,
            int(user_id),
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_send_polls=True,
                can_add_web_page_previews=True
            ),
            message_thread_id=update.message.message_thread_id if update.message else None
        )
        message.reply_text(f"Unmuted {mention_html(member.user.id, member.user.first_name)}!", parse_mode=ParseMode.HTML)
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#UNMUTE\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
        )

    except BadRequest as excp:
        if excp.message == "User is an administrator of the chat":
            message.reply_text("This user is an administrator and cannot be unmuted.", parse_mode=ParseMode.HTML)
            return ""
        elif excp.message == "Not enough rights to restrict/unrestrict chat member":
            message.reply_text("I don't have permission to unmute users in this chat!", parse_mode=ParseMode.HTML)
            return ""
        else:
            LOGGER.exception(f"Error unmuting user {user_id} in chat {chat.id}: {excp.message}")
            message.reply_text(f"Failed to unmute user: {excp.message}", parse_mode=ParseMode.HTML)
            return ""

    except Exception as e:
        LOGGER.exception(f"Unexpected error unmuting user {user_id} in chat {chat.id}: {str(e)}")
        message.reply_text(f"An unexpected error occurred: {str(e)}", parse_mode=ParseMode.HTML)
        return ""


@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_admin(update, user_id, member):
        message.reply_text("I really wish I could mute admins...")
        return ""

    if user_id == bot.id:
        message.reply_text("I'm not gonna MUTE myself, are you crazy?")
        return ""

    if not reason:
        message.reply_text(
            "You haven't specified a time to mute this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP MUTED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        if member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(
                chat.id,
                user_id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False))
            message.reply_text("Muted for {}!".format(time_val))
            return log
        else:
            message.reply_text("This user is already muted.")

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("Muted for {}!".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR muting user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Well damn, I can't mute that user.")

    return ""


__help__ = """
*Admin only:*
 - /mute <userhandle>: silences a user. Can also be used as a reply, muting the replied to user.
 - /tmute <userhandle> x(m/h/d): mutes a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
 - /unmute <userhandle>: unmutes a user. Can also be used as a reply, muting the replied to user.
"""

__mod_name__ = "Muting"

MUTE_HANDLER = CommandHandler("mute",
                              mute,
                              run_async=True,
                              filters=Filters.chat_type.groups)
UNMUTE_HANDLER = CommandHandler("unmute",
                                unmute,
                                run_async=True,
                                filters=Filters.chat_type.groups)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute"],
                                  temp_mute,
                                  run_async=True,
                                  filters=Filters.chat_type.groups)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)
