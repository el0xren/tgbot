import html
from typing import List, Optional

from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, CallbackContext, OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin, support_plus, validate_user
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_user_com_chats
import tg_bot.modules.sql.global_kicks_sql as sql

GKICK_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
    "Method is available for supergroup and channel chats only",
    "Reply message not found",
    "Bots can't add new chat members",
    "Can't demote chat creator",
    "Method is available only for supergroups",
    "Can't remove chat owner",
    "User not found",
    "Chat_id is empty",
}

@support_plus
def gkick(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args
    message = update.effective_message
    kicker = update.effective_user  # type: Optional[User]

    user_id, reason = extract_user_and_text(message, args)
    LOGGER.debug(f"gkick: user_id={user_id}, reason={reason}, kicker_id={kicker.id}")

    if not user_id:
        if message.reply_to_message:
            message.reply_text(
                "Cannot extract a user from this forwarded message (possibly a channel or anonymous admin). "
                "Please use @username or user ID.",
                parse_mode=ParseMode.HTML)
        else:
            message.reply_text(
                "You don't seem to be referring to a user. Reply to a message, use @username, or provide a user ID.",
                parse_mode=ParseMode.HTML)
        return ""

    if not reason:
        message.reply_text("You must provide a reason.", parse_mode=ParseMode.HTML)
        return ""

    user_chat = validate_user(update, context, user_id, kicker.id)
    if not user_chat:
        return ""

    message.reply_text("*Snaps with fingers* 😉", parse_mode=ParseMode.HTML)

    chats = get_user_com_chats(user_id)
    kicked_chats = []
    for chat in chats:
        try:
            bot.unban_chat_member(chat, user_id)
            kicked_chats.append(chat)
        except BadRequest as excp:
            if excp.message in GKICK_ERRORS:
                pass
            else:
                message.reply_text(
                    f"User cannot be globally kicked because: {excp.message}", parse_mode=ParseMode.HTML)
                return ""
        except TelegramError as excp:
            LOGGER.warning(f"TelegramError in gkick for chat {chat}: {excp.message}")
            pass

    if kicked_chats:
        log = "<b>Global Kick</b>" \
              "\n#GKICK" \
              "\n<b>Status:</b> <code>Enforcing</code>" \
              "\n<b>Sudo Admin:</b> {}" \
              "\n<b>User:</b> {}" \
              "\n<b>ID:</b> <code>{}</code>" \
              "\n<b>Chats:</b> <code>{}</code>".format(
                  mention_html(kicker.id, kicker.first_name),
                  mention_html(user_chat.id, user_chat.first_name),
                  user_chat.id,
                  len(kicked_chats))
        if reason:
            log += "\n<b>Reason:</b> {}".format(reason)

        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log, html=True)
        message.reply_text(
            f"Done! Gkicked.\n<b>ID:</b> <code>{user_id}</code>\n<b>Chats:</b> <code>{len(kicked_chats)}</code>",
            parse_mode=ParseMode.HTML)
        return log
    else:
        message.reply_text("Failed to kick user from any chats.", parse_mode=ParseMode.HTML)
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                     f"Failed to globally kick user {user_chat.first_name} ({user_id}): No chats affected.",
                     html=True)
        return ""

@support_plus
def gkickset(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args
    message = update.effective_message
    kicker = update.effective_user  # type: Optional[User]
    user_id, value = extract_user_and_text(message, args)

    LOGGER.debug(f"gkickset: user_id={user_id}, value={value}, kicker_id={kicker.id}")

    if not user_id:
        if message.reply_to_message:
            message.reply_text(
                "Cannot extract a user from this forwarded message (possibly a channel or anonymous admin). "
                "Please use @username or user ID.",
                parse_mode=ParseMode.HTML)
        else:
            message.reply_text(
                "You don't seem to be referring to a user. Reply to a message, use @username, or provide a user ID.",
                parse_mode=ParseMode.HTML)
        return ""

    user_chat = validate_user(update, context, user_id, kicker.id)
    if not user_chat:
        return ""

    if not value:
        message.reply_text("You must provide a value to set.", parse_mode=ParseMode.HTML)
        return ""

    if not value.strip().isdigit():
        message.reply_text("Value must be a number!", parse_mode=ParseMode.HTML)
        return ""

    value = int(value.strip())
    try:
        sql.gkick_setvalue(user_id, user_chat.username or str(user_id), value)
        message.reply_text(
            f"Set gkick value for {mention_html(user_chat.id, user_chat.first_name)} to {value}.",
            parse_mode=ParseMode.HTML)
        return ""
    except Exception as excp:
        LOGGER.error(f"Error setting gkick value for user {user_id}: {excp}")
        message.reply_text(f"Failed to set gkick value: {str(excp)}", parse_mode=ParseMode.HTML)
        return ""

@support_plus
def gkickreset(update: Update, context: CallbackContext) -> Optional[str]:
    args = context.args
    message = update.effective_message
    kicker = update.effective_user  # type: Optional[User]
    user_id, _ = extract_user_and_text(message, args)

    LOGGER.debug(f"gkickreset: user_id={user_id}, kicker_id={kicker.id}")

    if not user_id:
        if message.reply_to_message:
            message.reply_text(
                "Cannot extract a user from this forwarded message (possibly a channel or anonymous admin). "
                "Please use @username or user ID.",
                parse_mode=ParseMode.HTML)
        else:
            message.reply_text(
                "You don't seem to be referring to a user. Reply to a message, use @username, or provide a user ID.",
                parse_mode=ParseMode.HTML)
        return ""

    user_chat = validate_user(update, context, user_id, kicker.id)
    if not user_chat:
        return ""

    try:
        sql.gkick_reset(user_id)
        message.reply_text(
            f"Reset gkick for {mention_html(user_chat.id, user_chat.first_name)}.",
            parse_mode=ParseMode.HTML)
        return ""
    except Exception as excp:
        LOGGER.error(f"Error resetting gkick for user {user_id}: {excp}")
        message.reply_text(f"Failed to reset gkick: {str(excp)}", parse_mode=ParseMode.HTML)
        return ""

def __user_info__(user_id):
    times = sql.get_times(user_id)

    text = "<b>Globally Kicked</b>: {}"
    if times != 0:
        text = text.format(
            "<code>Yes</code> (Times: <code>{}</code>)".format(times))
    else:
        text = text.format("<code>No</code>")

    return text

__help__ = """
*Support users only:*
 - /gkick <userhandle> <reason>: Globally kicks a user from all common chats with a reason
 - /gkickset <userhandle> <value>: Sets a gkick value for a user (e.g., number of kicks)
 - /gkickreset <userhandle>: Resets a user's gkick status
"""

GKICK_HANDLER = CommandHandler("gkick", gkick, run_async=True)
SET_HANDLER = CommandHandler("gkickset", gkickset, run_async=True)
RESET_HANDLER = CommandHandler("gkickreset", gkickreset, run_async=True)

dispatcher.add_handler(GKICK_HANDLER)
dispatcher.add_handler(SET_HANDLER)
dispatcher.add_handler(RESET_HANDLER)