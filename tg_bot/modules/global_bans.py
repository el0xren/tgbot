import html
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.global_bans_sql as sql
from tg_bot import dispatcher, CallbackContext, OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN, SUPPORT_CHAT, LOGS
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin, support_plus
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
}


@support_plus
def gban(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    args = context.args
    message: Optional[Message] = update.effective_message

    sender_id: int = update.effective_user.id
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    if not reason:
        message.reply_text("You must provide a reason.")
        return

    if user_id == sender_id:
        message.reply_text("You cannot ban yourself.")
        return

    if int(user_id) == OWNER_ID:
        message.reply_text("You cannot ban the bot owner.")
        return
    if int(user_id) in DEV_USERS:
        message.reply_text("This user is a developer and cannot be banned.")
        return
    if int(user_id) in SUDO_USERS:
        message.reply_text("This user is a sudo user and cannot be banned.")
        return
    if int(user_id) in SUPPORT_USERS:
        message.reply_text("This user is a support user and cannot be banned.")
        return
    if user_id == bot.id:
        message.reply_text("I cannot ban myself.")
        return

    try:
        user_chat = bot.get_chat(user_id)
        if user_chat.type != 'private':
            message.reply_text("That's not a user.")
            return
    except BadRequest as excp:
        message.reply_text(f"Error fetching user: {excp.message}")
        return

    if sql.is_user_gbanned(user_id):
        if not reason:
            message.reply_text(
                "This user is already gbanned; I'd change the reason, but you haven't given me one..."
            )
            return

        old_reason = sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason)
        user_id, new_reason = extract_user_and_text(message, args)
        if old_reason:
            banner = update.effective_user  # type: Optional[User]
            log = "<b>Emendation of Global Ban</b>" \
                  "\n#GBAN" \
                  "\n<b>Status:</b> <code>Amended</code>" \
                  "\n<b>Sudo Admin:</b> {}" \
                  "\n<b>User:</b> {}" \
                  "\n<b>ID:</b> <code>{}</code>" \
                  "\n<b>Initiated From:</b> <code>{}</code>" \
                  "\n<b>Previous Reason:</b> {}" \
                  "\n<b>Amended Reason:</b> {}".format(mention_html(banner.id, banner.first_name),
                                                       mention_html(user_chat.id, user_chat.first_name or "Deleted Account"),
                                                                    user_chat.id,message.chat.title, old_reason, new_reason)
            if LOGS:
                bot.send_message(LOGS, log, parse_mode=ParseMode.HTML)
            else:
                send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log, html=True)

            message.reply_text(
                "This user is already gbanned, for the following reason:\n"
                "<code>{}</code>\n"
                "I've gone and updated it with your new reason!".format(
                    html.escape(old_reason)),
                parse_mode=ParseMode.HTML)
        else:
            banner = update.effective_user  # type: Optional[User]
            log = "<b>Emendation of Global Ban</b>" \
                  "\n#GBAN" \
                  "\n<b>Status:</b> <code>New reason</code>" \
                  "\n<b>Sudo Admin:</b> {}" \
                  "\n<b>User:</b> {}" \
                  "\n<b>ID:</b> <code>{}</code>" \
                  "\n<b>Initiated From:</b> <code>{}</code>" \
                  "\n<b>New Reason:</b> {}".format(mention_html(banner.id, banner.first_name),
                                                   mention_html(user_chat.id, user_chat.first_name or "Deleted Account"),
                                                                user_chat.id, message.chat.title, new_reason)
            if LOGS:
                bot.send_message(LOGS, log, parse_mode=ParseMode.HTML)
            else:
                send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log, html=True)

            message.reply_text(
                "This user is already gbanned, but had no reason set; I've gone and updated it!"
            )

        return

    message.reply_text("*Blows dust off of banhammer* 😉")

    banner = update.effective_user  # type: Optional[User]
    log = "<b>Global Ban</b>" \
          "\n#GBAN" \
          "\n<b>Status:</b> <code>Enforcing</code>" \
          "\n<b>Sudo Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>ID:</b> <code>{}</code>" \
          "\n<b>Initiated From:</b> <code>{}</code>" \
          "\n<b>Reason:</b> {}".format(mention_html(banner.id, banner.first_name),
                                       mention_html(user_chat.id, user_chat.first_name or "Deleted Account"),
                                                    user_chat.id, message.chat.title, reason or "No reason given")
    if LOGS:
        bot.send_message(LOGS, log, parse_mode=ParseMode.HTML)
    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log, html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_user_com_chats(user_id)
    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text("Could not gban due to: {}".format(
                    excp.message))
                if LOGS:
                    bot.send_message(LOGS,
                                     "Could not gban due to {}".format(
                                         excp.message),
                                     parse_mode=ParseMode.HTML)
                else:
                    send_to_list(
                        bot, SUDO_USERS + SUPPORT_USERS,
                        "Could not gban due to: {}".format(excp.message))
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    message.reply_text(
        "Done! Gbanned.\n<b>ID:</b> <code>{}</code>".format(user_id),
        parse_mode=ParseMode.HTML)
    try:
        bot.send_message(
            user_id,
            f"You have been globally banned from all groups where I have administrative permissions. If you think that this was a mistake, you may appeal your ban here: @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML)
    except:
        pass


@support_plus
def ungban(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("This user is not gbanned!")
        return

    banner = update.effective_user  # type: Optional[User]

    message.reply_text("I'll give {} a second chance, globally.".format(
        user_chat.first_name))

    log = "<b>Regression of Global Ban</b>" \
          "\n#UNGBAN" \
          "\n<b>Status:</b> <code>Ceased</code>" \
          "\n<b>Sudo Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>Initiated From:</b> <code>{}</code>" \
          "\n<b>ID:</b> <code>{}</code>".format(mention_html(banner.id, banner.first_name),
                                                mention_html(user_chat.id, user_chat.first_name or "Deleted Account"),
                                                             message.chat.title, user_chat.id)
    if LOGS:
        bot.send_message(LOGS, log, parse_mode=ParseMode.HTML)
    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log, html=True)

    chats = get_user_com_chats(user_id)
    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
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
                message.reply_text("Could not un-gban due to: {}".format(
                    excp.message))
                bot.send_message(
                    OWNER_ID,
                    "Could not un-gban due to: {}".format(excp.message))
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    message.reply_text("Person has been un-gbanned.")


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
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    if sql.does_chat_gban(
            update.effective_chat.id) and update.effective_chat.get_member(
                bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(update, user.id):
            check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)
            return

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(update, user.id):
                check_and_ban(update, user.id, should_message=False)
                return


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
