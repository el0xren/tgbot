import html
import json
import os
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, CallbackContext, OWNER_ID, DEV_USERS, SUDO_USERS,  SUPPORT_USERS, WHITELIST_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, can_promote, user_admin, can_pin, sudo_plus, dev_plus
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.log_channel import loggable


@dev_plus
@loggable
def addsudo(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'r') as infile:
        data = json.load(infile)
    if user_id in SUDO_USERS:
        message.reply_text("This member is already sudo")
        return ""
    if user_id in SUPPORT_USERS:
        message.reply_text("This user is already a support user. Promoting to sudo.")
        data['supports'].remove(user_id)
        SUPPORT_USERS.remove(user_id)
    if user_id in WHITELIST_USERS:
        message.reply_text("This user is already a whitelisted user. Promoting to sudo.")
        data['whitelists'].remove(user_id)
        WHITELIST_USERS.remove(user_id)
    data['sudos'].append(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'w') as outfile:
        json.dump(data, outfile, indent=4)
    SUDO_USERS.append(user_id)
    update.effective_message.reply_text("Successfully set privilege level {} to sudo!".format(user_member.user.first_name))
    return "<b>{}:</b>" \
           "\n#SUDO" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@dev_plus
@loggable
def removesudo(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'r') as infile:
        data = json.load(infile)
    if user_id in SUDO_USERS:
        message.reply_text("Demoting to normal user")
        SUDO_USERS.remove(user_id)
        data['sudos'].remove(user_id)
        with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'w') as outfile:
            json.dump(data, outfile, indent=4)
        return "<b>{}:</b>" \
           "\n#UNSUDO" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))
    else:
        message.reply_text("This user is not a sudo!")
        return ""


@dev_plus
@loggable
def addsupport(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'r') as infile:
        data = json.load(infile)
    if user_id in SUDO_USERS:
        message.reply_text("This member is a sudo user. Demoting to support.")
        data['sudos'].remove(user_id)
        SUDO_USERS.remove(user_id)
    if user_id in SUPPORT_USERS:
        message.reply_text("This user is already a support user.")
        return ""
    if user_id in WHITELIST_USERS:
        message.reply_text("This user is already a whitelisted user. Promoting to support.")
        data['whitelists'].remove(user_id)
        WHITELIST_USERS.remove(user_id)
    data['supports'].append(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'w') as outfile:
        json.dump(data, outfile, indent=4)
    SUPPORT_USERS.append(user_id)
    update.effective_message.reply_text("Successfully set privilege level {} to support!".format(user_member.user.first_name))
    return "<b>{}:</b>" \
           "\n#SUPPORT" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@dev_plus
@loggable
def removesupport(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'r') as infile:
        data = json.load(infile)
    if user_id in SUPPORT_USERS:
        message.reply_text("Demoting to normal user")
        SUPPORT_USERS.remove(user_id)
        data['supports'].remove(user_id)
        with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'w') as outfile:
            json.dump(data, outfile, indent=4)
        return "<b>{}:</b>" \
           "\n#UNSUPPORT" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))
    else:
        message.reply_text("This user is not a support user!")
        return ""


@dev_plus
@loggable
def addwhitelist(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'r') as infile:
        data = json.load(infile)
    if user_id in SUDO_USERS:
        message.reply_text("This member is a sudo user. Demoting to whitelist.")
        data['sudos'].remove(user_id)
        SUDO_USERS.remove(user_id)
    if user_id in SUPPORT_USERS:
        message.reply_text("This user is already a support user. Demoting to whitelist.")
        data['supports'].remove(user_id)
        SUPPORT_USERS.remove(user_id)
    if user_id in WHITELIST_USERS:
        message.reply_text("This user is already a whitelisted user.")
        return ""
    data['whitelists'].append(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'w') as outfile:
        json.dump(data, outfile, indent=4)
    WHITELIST_USERS.append(user_id)
    update.effective_message.reply_text("Successfully set privilege level {} to whitelist!".format(user_member.user.first_name))
    return "<b>{}:</b>" \
           "\n#WHITELIST" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@dev_plus
@loggable
def removewhitelist(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'r') as infile:
        data = json.load(infile)
    if user_id in WHITELIST_USERS:
        message.reply_text("Demoting to normal user")
        WHITELIST_USERS.remove(user_id)
        data['whitelists'].remove(user_id)
        with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'w') as outfile:
            json.dump(data, outfile, indent=4)
        return "<b>{}:</b>" \
           "\n#UNWHITELIST" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))
    else:
        message.reply_text("This user is not a whitelisted user!")
        return ""


@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    chat_id = update.effective_chat.id
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == 'administrator' or user_member.status == 'creator':
        message.reply_text("How am I meant to promote someone that's already an admin?")
        return ""

    if user_id == bot.id:
        message.reply_text("I can't promote myself! Get an admin to do it for me.")
        return ""

    bot_member = chat.get_member(bot.id)

    bot.promoteChatMember(chat_id, user_id,
                          can_change_info=bot_member.can_change_info,
                          can_post_messages=bot_member.can_post_messages,
                          can_edit_messages=bot_member.can_edit_messages,
                          can_delete_messages=bot_member.can_delete_messages,
                          # can_invite_users=bot_member.can_invite_users,
                          can_restrict_members=bot_member.can_restrict_members,
                          can_pin_messages=bot_member.can_pin_messages,
                          can_promote_members=bot_member.can_promote_members)

    message.reply_text("Successfully promoted!")
    return "<b>{}:</b>" \
           "\n#PROMOTED" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@bot_admin
@can_promote
@user_admin
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == 'creator':
        message.reply_text("This person CREATED the chat, how would I demote them?")
        return ""

    if not user_member.status == 'administrator':
        message.reply_text("Can't demote what wasn't promoted!")
        return ""

    if user_id == bot.id:
        message.reply_text("I can't demote myself! Get an admin to do it for me.")
        return ""

    try:
        bot.promoteChatMember(int(chat.id), int(user_id),
                              can_change_info=False,
                              can_post_messages=False,
                              can_edit_messages=False,
                              can_delete_messages=False,
                              can_invite_users=False,
                              can_restrict_members=False,
                              can_pin_messages=False,
                              can_promote_members=False)
        message.reply_text("Successfully demoted!")
        return "<b>{}:</b>" \
               "\n#DEMOTED" \
               "\n<b>Admin:</b> {}" \
               "\n<b>User:</b> {}".format(html.escape(chat.title),
                                          mention_html(user.id, user.first_name),
                                          mention_html(user_member.user.id, user_member.user.first_name))

    except BadRequest:
        message.reply_text("Could not demote. I might not be admin, or the admin status was appointed by another "
                           "user, so I can't act upon them!")
        return ""


@bot_admin
@can_pin
@user_admin
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    is_group = chat.type != "private" and chat.type != "channel"

    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower() == 'loud' or args[0].lower() == 'violent')

    if prev_message and is_group:
        try:
            bot.pinChatMessage(chat.id, prev_message.message_id, disable_notification=is_silent)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        return "<b>{}:</b>" \
               "\n#PINNED" \
               "\n<b>Admin:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name))

    return ""


@bot_admin
@can_pin
@user_admin
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user  # type: Optional[User]

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    return "<b>{}:</b>" \
           "\n#UNPINNED" \
           "\n<b>Admin:</b> {}".format(html.escape(chat.title),
                                       mention_html(user.id, user.first_name))


@bot_admin
@user_admin
def invite(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    if chat.username:
        update.effective_message.reply_text(chat.username)
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text("I don't have access to the invite link, try changing my permissions!")
    else:
        update.effective_message.reply_text("I can only give you invite links for supergroups and channels, sorry!")


def adminlist(update: Update, context: CallbackContext):
    bot = context.bot
    administrators = update.effective_chat.get_administrators()
    text = "Admins in *{}*:".format(update.effective_chat.title or "this chat")
    for admin in administrators:
        user = admin.user
        name = "[{}](tg://user?id={})".format(user.first_name + (user.last_name or ""), user.id)
        if user.username:
            name = escape_markdown("@" + user.username)
        text += "\n - {}".format(name)

    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def __chat_settings__(chat_id, user_id):
    return "You are *admin*: `{}`".format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status in ("administrator", "creator"))


__help__ = """
 - /adminlist: list of admins in the chat

*Admin only:*
 - /pin: silently pins the message replied to - add 'loud' or 'notify' to give notifs to users.
 - /unpin: unpins the currently pinned message
 - /invitelink: gets invitelink
 - /promote: promotes the user replied to
 - /demote: demotes the user replied to
"""

__mod_name__ = "Admin"

PIN_HANDLER = CommandHandler("pin", pin, pass_args=True, filters=Filters.chat_type.groups, run_async=True)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.chat_type.groups, run_async=True)

INVITE_HANDLER = CommandHandler("invitelink", invite, filters=Filters.chat_type.groups, run_async=True)

PROMOTE_HANDLER = CommandHandler("promote", promote, pass_args=True, filters=Filters.chat_type.groups, run_async=True)
DEMOTE_HANDLER = CommandHandler("demote", demote, pass_args=True, filters=Filters.chat_type.groups, run_async=True)

ADMINLIST_HANDLER = DisableAbleCommandHandler("adminlist", adminlist, filters=Filters.chat_type.groups, run_async=True)

SUDO_HANDLER = CommandHandler("addsudo", addsudo, pass_args=True, filters=Filters.chat_type.groups, run_async=True)
UNSUDO_HANDLER = CommandHandler("removesudo", removesudo, pass_args=True, filters=Filters.chat_type.groups, run_async=True)
SUPPORT_HANDLER = CommandHandler("addsupport", addsupport, pass_args=True, filters=Filters.chat_type.groups, run_async=True)
UNSUPPORT_HANDLER = CommandHandler("removesupport", removesupport, pass_args=True, filters=Filters.chat_type.groups, run_async=True)
WHITELIST_HANDLER = CommandHandler("addwhitelist", addwhitelist, pass_args=True, filters=Filters.chat_type.groups, run_async=True)
UNWHITELIST_HANDLER = CommandHandler("removewhitelist", removewhitelist, pass_args=True, filters=Filters.chat_type.groups, run_async=True)

dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(SUDO_HANDLER)
dispatcher.add_handler(UNSUDO_HANDLER)
dispatcher.add_handler(SUPPORT_HANDLER)
dispatcher.add_handler(UNSUPPORT_HANDLER)
dispatcher.add_handler(WHITELIST_HANDLER)
dispatcher.add_handler(UNWHITELIST_HANDLER)
