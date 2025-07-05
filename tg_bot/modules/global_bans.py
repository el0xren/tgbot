import html
import traceback
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError, Unauthorized
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.global_bans_sql as sql
from tg_bot import dispatcher, CallbackContext, OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN, SUPPORT_CHAT, LOGS
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin, support_plus, validate_user
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_user_com_chats

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
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
    "Can't remove chat owner",
    "Method is available for supergroup and channel chats only",
    "User not found",
    "Method is available only for supergroups",
    "Bots can't add new chat members",
    "Can't demote chat creator",
    "Reply message not found",
    "Chat_id is empty",
    "Forbidden: bot was blocked by the user",
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
    "User not found",
    "Can't remove chat owner",
    "Can't demote chat creator",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Only the creator of a basic group can kick group administrators",
    "Chat_id is empty",
    "Forbidden: bot was blocked by the user",
}


@support_plus
def gban(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    args = context.args
    message = update.effective_message
    banner = update.effective_user

    user_id, reason = extract_user_and_text(message, args)

    if not reason:
        message.reply_text("You must provide a reason.", parse_mode=ParseMode.HTML)
        return

    user_chat = validate_user(update, context, user_id, banner.id)
    if not user_chat:
        return

    if user_chat.type != 'private':
        message.reply_text("That's not a user.", parse_mode=ParseMode.HTML)
        return

    if sql.is_user_gbanned(user_id):
        old_reason = sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason)

        _, new_reason = extract_user_and_text(message, args)
        if old_reason:
            log = "<b>Emendation of Global Ban</b>" \
                  "\n#GBAN" \
                  "\n<b>Status:</b> <code>Amended</code>" \
                  "\n<b>Sudo Admin:</b> {}" \
                  "\n<b>User:</b> {}" \
                  "\n<b>ID:</b> <code>{}</code>" \
                  "\n<b>Initiated From:</b> <code>{}</code>" \
                  "\n<b>Previous Reason:</b> {}" \
                  "\n<b>Amended Reason:</b> {}".format(
                      mention_html(banner.id, banner.first_name),
                      mention_html(user_chat.id, user_chat.first_name or "Deleted Account"),
                      user_chat.id, message.chat.title, old_reason, new_reason)
            if LOGS:
                bot.send_message(LOGS, log, parse_mode=ParseMode.HTML)
            else:
                send_to_list(bot, SUPPORT_USERS + SUDO_USERS + DEV_USERS, log, html=True)

            message.reply_text(
                "This user is already gbanned, for the following reason:\n"
                "<code>{}</code>\n"
                "I've gone and updated it with your new reason!".format(
                    html.escape(old_reason)),
                parse_mode=ParseMode.HTML)
        else:
            log = "<b>Emendation of Global Ban</b>" \
                  "\n#GBAN" \
                  "\n<b>Status:</b> <code>New reason</code>" \
                  "\n<b>Sudo Admin:</b> {}" \
                  "\n<b>User:</b> {}" \
                  "\n<b>ID:</b> <code>{}</code>" \
                  "\n<b>Initiated From:</b> <code>{}</code>" \
                  "\n<b>New Reason:</b> {}".format(
                      mention_html(banner.id, banner.first_name),
                      mention_html(user_chat.id, user_chat.first_name or "Deleted Account"),
                      user_chat.id, message.chat.title, new_reason)
            if LOGS:
                bot.send_message(LOGS, log, parse_mode=ParseMode.HTML)
            else:
                send_to_list(bot, SUPPORT_USERS + SUDO_USERS + DEV_USERS, log, html=True)

            message.reply_text(
                "This user is already gbanned, but had no reason set; I've gone and updated it!",
                parse_mode=ParseMode.HTML)
        return

    message.reply_text("*Blows dust off of banhammer* 😉", parse_mode=ParseMode.HTML)

    log = "<b>Global Ban</b>" \
          "\n#GBAN" \
          "\n<b>Status:</b> <code>Enforcing</code>" \
          "\n<b>Sudo Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>ID:</b> <code>{}</code>" \
          "\n<b>Initiated From:</b> <code>{}</code>" \
          "\n<b>Reason:</b> {}".format(
              mention_html(banner.id, banner.first_name),
              mention_html(user_chat.id, user_chat.first_name or "Deleted Account"),
              user_chat.id, message.chat.title, reason or "No reason given")
    if LOGS:
        bot.send_message(LOGS, log, parse_mode=ParseMode.HTML)
    else:
        send_to_list(bot, SUPPORT_USERS + SUDO_USERS + DEV_USERS, log, html=True)

    try:
        sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)
    except Exception as excp:
        message.reply_text(f"Failed to set gban: {str(excp)}", parse_mode=ParseMode.HTML)
        return

    chats = get_user_com_chats(user_id)
    for chat in chats:
        chat_id = int(chat)

        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text(f"Could not gban due to: {excp.message}", parse_mode=ParseMode.HTML)
                if LOGS:
                    bot.send_message(LOGS,
                                     f"Could not gban due to {excp.message}",
                                     parse_mode=ParseMode.HTML)
                else:
                    send_to_list(
                        bot, SUPPORT_USERS + SUDO_USERS + DEV_USERS,
                        f"Could not gban due to: {excp.message}")
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    message.reply_text(
        f"Done! Gbanned.\n<b>ID:</b> <code>{user_id}</code>",
        parse_mode=ParseMode.HTML)
    try:
        bot.send_message(
            user_id,
            f"You have been globally banned from all groups where I have administrative permissions. "
            f"If you think that this was a mistake, you may appeal your ban here: @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML)
    except:
        pass


@support_plus
def ungban(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    args = context.args
    message = update.effective_message
    banner = update.effective_user

    user_id = extract_user(message, args)

    user_chat = validate_user(update, context, user_id, banner.id)
    if not user_chat:
        return

    if user_chat.type != 'private':
        message.reply_text("That's not a user!", parse_mode=ParseMode.HTML)
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("This user is not gbanned!", parse_mode=ParseMode.HTML)
        return

    message.reply_text(
        f"I'll give {html.escape(user_chat.first_name)} a second chance, globally.",
        parse_mode=ParseMode.HTML)

    log = "<b>Regression of Global Ban</b>" \
          "\n#UNGBAN" \
          "\n<b>Status:</b> <code>Ceased</code>" \
          "\n<b>Sudo Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>Initiated From:</b> <code>{}</code>" \
          "\n<b>ID:</b> <code>{}</code>".format(
              mention_html(banner.id, banner.first_name),
              mention_html(user_chat.id, user_chat.first_name or "Deleted Account"),
              message.chat.title, user_chat.id)
    if LOGS:
        bot.send_message(LOGS, log, parse_mode=ParseMode.HTML)
    else:
        send_to_list(bot, SUPPORT_USERS + SUDO_USERS + DEV_USERS, log, html=True)

    chats = get_user_com_chats(user_id)
    for chat in chats:
        chat_id = int(chat)

        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text(f"Could not un-gban due to: {excp.message}", parse_mode=ParseMode.HTML)
                bot.send_message(
                    OWNER_ID,
                    f"Could not un-gban due to: {excp.message}",
                    parse_mode=ParseMode.HTML)
                return
        except TelegramError:
            pass

    try:
        sql.ungban_user(user_id)
    except Exception as excp:
        message.reply_text(f"Failed to un-gban: {str(excp)}", parse_mode=ParseMode.HTML)
        return

    message.reply_text("Person has been un-gbanned.", parse_mode=ParseMode.HTML)


@support_plus
def gbanlist(update: Update, context: CallbackContext):
    bot = context.bot
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(
            "There aren't any gbanned users! You're kinder than I expected...")
        return

    banfile = 'Screw these guys.\n'
    for user in banned_users:
        banfile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            banfile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Here is the list of currently gbanned users.")


def check_and_ban(update, user_id, should_message=True):
    if sql.is_user_gbanned(user_id):
        update.effective_chat.ban_member(user_id)
        if should_message:
            update.effective_message.reply_text(
                "This is a bad person, they shouldn't be here!")


def enforce_gban(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message

    try:
        if sql.does_chat_gban(chat.id) and chat.get_member(bot.id).can_restrict_members:
            user = update.effective_user

            if user and not is_user_admin(update, user.id):
                check_and_ban(update, user.id)
                return

            if msg.new_chat_members:
                for mem in msg.new_chat_members:
                    check_and_ban(update, mem.id)
                return

            if msg.reply_to_message:
                user = msg.reply_to_message.from_user
                if user and not is_user_admin(update, user.id):
                    check_and_ban(update, user.id, should_message=False)
                    return

    except Unauthorized as e:
        log = (
            f"<b>Bot was kicked or unauthorized in chat</b>\n"
            f"<b>Chat ID:</b> <code>{chat.id}</code>\n"
            f"<b>Error:</b> <code>{str(e)}</code>"
        )
        send_to_list(bot, SUPPORT_USERS + SUDO_USERS + DEV_USERS, log, html=True)

    except TelegramError as e:
        log = (
            f"<b>TelegramError in enforce_gban</b>\n"
            f"<b>Chat ID:</b> <code>{chat.id}</code>\n"
            f"<b>Type:</b> <code>{type(e).__name__}</code>\n"
            f"<b>Message:</b> <code>{e}</code>"
        )
        send_to_list(bot, SUPPORT_USERS + SUDO_USERS + DEV_USERS, log, html=True)

    except Exception as e:
        tb = traceback.format_exc()
        log = (
            f"<b>Unexpected Exception in enforce_gban</b>\n"
            f"<b>Chat ID:</b> <code>{chat.id if chat else 'unknown'}</code>\n"
            f"<b>Traceback:</b>\n<code>{tb}</code>"
        )
        send_to_list(bot, SUPPORT_USERS + SUDO_USERS + DEV_USERS, log, html=True)


@user_admin
def gbanstat(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've enabled gbans in this group. This will help protect you "
                "from spammers, unsavoury characters, and the biggest trolls.")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've disabled gbans in this group. GBans wont affect your users "
                "anymore. You'll be less protected from any trolls and spammers "
                "though!")
    else:
        update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any gbans that happen will also happen in your group. "
            "When False, they won't, leaving you at the possible mercy of "
            "spammers.".format(sql.does_chat_gban(update.effective_chat.id)))


def __stats__():
    return "{} gbanned users.".format(sql.num_gbanned_users())


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = "<b>Globally Banned</b>: <code>{}</code>"
    if is_gbanned:
        text = text.format("<code>Yes</code>")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += "\n  Reason: <code>{}</code>".format(
                html.escape(user.reason))
    else:
        text = text.format("<code>No</code>")

    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "This chat is enforcing *gbans*: `{}`.".format(
        sql.does_chat_gban(chat_id))


__help__ = """
*Admin only:*
 - /gbanstat <on/off/yes/no>: Will disable the effect of global bans on your group, or return your current settings.

Gbans, also known as global bans, are used by the bot owners to ban spammers across all groups. This helps protect \
you and your groups by removing spam flooders as quickly as possible. They can be disabled for you group by calling \
/gbanstat
"""

__mod_name__ = "Global Bans"

GBAN_HANDLER = CommandHandler("gban", gban, run_async=True)
UNGBAN_HANDLER = CommandHandler("ungban", ungban, run_async=True)
GBAN_LIST = CommandHandler("gbanlist", gbanlist, run_async=True)
GBAN_STATUS = CommandHandler("gbanstat",
                             gbanstat,
                             run_async=True,
                             filters=Filters.chat_type.groups)
GBAN_ENFORCER = MessageHandler(Filters.all & Filters.chat_type.groups,
                               enforce_gban,
                               run_async=True)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
