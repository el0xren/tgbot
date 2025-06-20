import html
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat, ParseMode, ChatPermissions
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.global_mutes_sql as sql
from tg_bot import dispatcher, CallbackContext, OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS, STRICT_GMUTE, SUPPORT_CHAT
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin, support_plus
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats

GMUTE_ENFORCE_GROUP = 6

GMUTE_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Method is available only for supergroups",
    "Channel_private",
    "Not in the chat",
    "Can't demote chat creator",
    "Can't remove chat owner",
    "Participant_id_invalid",
}

UNGMUTE_ERRORS = {
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
    "Replied message not found",
}


@support_plus
def gmute(update: Update, context: CallbackContext) -> None:
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
        message.reply_text("You cannot mute yourself.")
        return

    if int(user_id) == OWNER_ID:
        message.reply_text("You cannot mute the bot owner.")
        return
    if int(user_id) in DEV_USERS:
        message.reply_text("This user is a developer and cannot be muted.")
        return
    if int(user_id) in SUDO_USERS:
        message.reply_text("This user is a sudo user and cannot be muted.")
        return
    if int(user_id) in SUPPORT_USERS:
        message.reply_text("This user is a support user and cannot be muted.")
        return
    if user_id == bot.id:
        message.reply_text("I cannot mute myself.")
        return

    try:
        user_chat = bot.get_chat(user_id)
        if user_chat.type != 'private':
            message.reply_text("That's not a user.")
            return
    except BadRequest as excp:
        message.reply_text(f"Error fetching user: {excp.message}")
        return


    if sql.is_user_gmuted(user_id):
        if not reason:
            message.reply_text(
                "This user is already gmuted; I'd change the reason, but you haven't given me one..."
            )
            return

        old_reason = sql.update_gmute_reason(
            user_id, user_chat.username or user_chat.first_name, reason)
        user_id, new_reason = extract_user_and_text(message, args)
        if old_reason:
            muter = update.effective_user  # type: Optional[User]
            send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                         "<b>Emendation of Global Mute</b>" \
                         "\n#GMUTE" \
                         "\n<b>Status:</b> <code>Amended</code>" \
                         "\n<b>Sudo Admin:</b> {}" \
                         "\n<b>User:</b> {}" \
                         "\n<b>ID:</b> <code>{}</code>" \
                         "\n<b>Initiated From:</b> <code>{}</code>" \
                         "\n<b>Previous Reason:</b> {}" \
                         "\n<b>Amended Reason:</b> {}".format(mention_html(muter.id, muter.first_name),
                                                              mention_html(user_chat.id, user_chat.first_name or "Deleted Account"),
                                                                           user_chat.id, message.chat.title, old_reason, new_reason),
                         html=True)

            message.reply_text(
                "This user is already gmuted, for the following reason:\n"
                "<code>{}</code>\n"
                "I've gone and updated it with your new reason!".format(
                    html.escape(old_reason)),
                parse_mode=ParseMode.HTML)
        else:
            muter = update.effective_user  # type: Optional[User]
            send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                         "<b>Emendation of Global Mute</b>" \
                         "\n#GMUTE" \
                         "\n<b>Status:</b> <code>New reason</code>" \
                         "\n<b>Sudo Admin:</b> {}" \
                         "\n<b>User:</b> {}" \
                         "\n<b>ID:</b> <code>{}</code>" \
                         "\n<b>Initiated From:</b> <code>{}</code>" \
                         "\n<b>New Reason:</b> {}".format(mention_html(muter.id, muter.first_name),
                                                          mention_html(user_chat.id, user_chat.first_name or "Deleted Account"),
                                                                       user_chat.id, message.chat.title, new_reason),
                         html=True)

            message.reply_text(
                "This user is already gmuted, but had no reason set; I've gone and updated it!"
            )

        return

    message.reply_text("*Gets duct tape* 😉")

    muter = update.effective_user  # type: Optional[User]
    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "<b>Global Mute</b>" \
                 "\n#GMUTE" \
                 "\n<b>Status:</b> <code>Enforcing</code>" \
                 "\n<b>Sudo Admin:</b> {}" \
                 "\n<b>User:</b> {}" \
                 "\n<b>ID:</b> <code>{}</code>" \
                 "\n<b>Initiated From:</b> <code>{}</code>" \
                 "\n<b>Reason:</b> {}".format(mention_html(muter.id, muter.first_name),
                                              mention_html(user_chat.id, user_chat.first_name or "Deleted Account"),
                                                           user_chat.id, message.chat.title, reason or "No reason given"),
                 html=True)

    sql.gmute_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gmutes
        if not sql.does_chat_gmute(chat_id):
            continue

        try:
            bot.restrict_chat_member(
                chat_id,
                user_id,
                permissions=ChatPermissions(can_send_messages=False))
        except BadRequest as excp:
            if excp.message in GMUTE_ERRORS:
                pass
            else:
                message.reply_text("Could not gmute due to: {}".format(
                    excp.message))
                send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                             "Could not gmute due to: {}".format(excp.message))
                sql.ungmute_user(user_id)
                return
        except TelegramError:
            pass

    send_to_list(bot,
                 SUDO_USERS + SUPPORT_USERS,
                 "{} has been gmuted.".format(
                     mention_html(user_chat.id, user_chat.first_name
                                  or "Deleted Account")),
                 html=True)

    message.reply_text(
        "Done! Gmuted.\n<b>ID:</b> <code>{}</code>".format(user_id),
        parse_mode=ParseMode.HTML)
    try:
        bot.send_message(
            user_id,
            f"You have been globally muted from all groups where I have administrative permissions. If you think that this was a mistake, you may appeal your mute here: @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML)
    except:
        pass


@support_plus
def ungmute(update: Update, context: CallbackContext):
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

    if not sql.is_user_gmuted(user_id):
        message.reply_text("This user is not gmuted!")
        return

    muter = update.effective_user  # type: Optional[User]

    message.reply_text("I'll let {} speak again, globally.".format(
        user_chat.first_name))

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "<b>Regression of Global Mute</b>" \
                 "\n#UNGMUTE" \
                 "\n<b>Status:</b> <code>Ceased</code>" \
                 "\n<b>Sudo Admin:</b> {}" \
                 "\n<b>User:</b> {}" \
                 "\n<b>ID:</b> <code>{}</code>".format(mention_html(muter.id, muter.first_name),
                                                       mention_html(user_chat.id, user_chat.first_name or "Deleted Account"),
                                                                    user_chat.id),
                 html=True)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gmutes
        if not sql.does_chat_gmute(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'restricted':
                bot.restrict_chat_member(chat_id,
                                         int(user_id),
                                         permissions=ChatPermissions(
                                             can_send_messages=True,
                                             can_send_media_messages=True,
                                             can_send_other_messages=True,
                                             can_add_web_page_previews=True))

        except BadRequest as excp:
            if excp.message in UNGMUTE_ERRORS:
                pass
            else:
                message.reply_text("Could not un-gmute due to: {}".format(
                    excp.message))
                bot.send_message(
                    OWNER_ID,
                    "Could not un-gmute due to: {}".format(excp.message))
                return
        except TelegramError:
            pass

    sql.ungmute_user(user_id)

    send_to_list(bot,
                 SUDO_USERS + SUPPORT_USERS,
                 "{} has been un-gmuted.".format(
                     mention_html(user_chat.id, user_chat.first_name
                                  or "Deleted Account")),
                 html=True)

    message.reply_text("Person has been un-gmuted.")


@support_plus
def gmutelist(update: Update, context: CallbackContext):
    bot = context.bot
    muted_users = sql.get_gmute_list()

    if not muted_users:
        update.effective_message.reply_text(
            "There aren't any gmuted users! You're kinder than I expected...")
        return

    mutefile = 'Screw these guys.\n'
    for user in muted_users:
        mutefile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            mutefile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(mutefile)) as output:
        output.name = "gmutelist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gmutelist.txt",
            caption="Here is the list of currently gmuted users.")


def check_and_mute(update, user_id, should_message=True):
    if sql.is_user_gmuted(user_id):
        bot.restrict_chat_member(update.effective_chat.id,
                                 user_id,
                                 can_send_messages=False)
        if should_message:
            update.effective_message.reply_text(
                "This is a bad person, I'll silence them for you!")


def enforce_gmute(update: Update, context: CallbackContext):
    bot = context.bot
    # Not using @restrict handler to avoid spamming - just ignore if cant gmute.
    if sql.does_chat_gmute(
            update.effective_chat.id) and update.effective_chat.get_member(
                bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_mute(update, user.id, should_message=True)
        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_mute(update, mem.id, should_message=True)
        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_mute(update, user.id, should_message=True)


@user_admin
def gmutestat(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gmutes(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've enabled gmutes in this group. This will help protect you "
                "from spammers, unsavoury characters, and the biggest trolls.")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gmutes(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've disabled gmutes in this group. GMutes wont affect your users "
                "anymore. You'll be less protected from any trolls and spammers "
                "though!")
    else:
        update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any gmutes that happen will also happen in your group. "
            "When False, they won't, leaving you at the possible mercy of "
            "spammers.".format(sql.does_chat_gmute(update.effective_chat.id)))


def __stats__():
    return "{} gmuted users.".format(sql.num_gmuted_users())


def __user_info__(user_id):
    is_gmuted = sql.is_user_gmuted(user_id)

    text = "<b>Globally Muted</b>: <code>{}</code>"
    if is_gmuted:
        text = text.format("<code>Yes</code>")
        user = sql.get_gmuted_user(user_id)
        if user.reason:
            text += "\n  Reason: <code>{}</code>".format(
                html.escape(user.reason))
    else:
        text = text.format("<code>No</code>")

    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "This chat is enforcing *gmutes*: `{}`.".format(
        sql.does_chat_gmute(chat_id))


__help__ = """
*Admin only:*
 - /gmutestat <on/off/yes/no>: Will disable the effect of global mutes on your group, or return your current settings.
Gmutes, also known as global mutes, are used by the bot owners to mute spammers across all groups. This helps protect \
you and your groups by removing spam flooders as quickly as possible. They can be disabled for you group by calling \
/gmutestat
"""

__mod_name__ = "Global Mutes"

GMUTE_HANDLER = CommandHandler("gmute", gmute, run_async=True)
UNGMUTE_HANDLER = CommandHandler("ungmute", ungmute, run_async=True)
GMUTE_LIST = CommandHandler("gmutelist", gmutelist, run_async=True)
GMUTE_STATUS = CommandHandler("gmutestat",
                              gmutestat,
                              run_async=True,
                              filters=Filters.chat_type.groups)
GMUTE_ENFORCER = MessageHandler(Filters.all & Filters.chat_type.groups,
                                enforce_gmute,
                                run_async=True)

dispatcher.add_handler(GMUTE_HANDLER)
dispatcher.add_handler(UNGMUTE_HANDLER)
dispatcher.add_handler(GMUTE_LIST)
dispatcher.add_handler(GMUTE_STATUS)

if STRICT_GMUTE:  # enforce GMUTES if this is set
    dispatcher.add_handler(GMUTE_ENFORCER, GMUTE_ENFORCE_GROUP)
