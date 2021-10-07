import html
import json
import os

from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, CallbackContext, OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS
from tg_bot.modules.helper_funcs.chat_status import sudo_plus, support_plus, whitelist_plus
from tg_bot.modules.log_channel import gloggable
from tg_bot.modules.helper_funcs.extraction import extract_user


@gloggable
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
    update.effective_message.reply_text("Successfully promoted {} to sudo!".format(user_member.user.first_name))
    return "<b>{}:</b>" \
           "\n#SUDO" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@gloggable
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


@gloggable
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
    update.effective_message.reply_text("Successfully promoted {} to support!".format(user_member.user.first_name))
    return "<b>{}:</b>" \
           "\n#SUPPORT" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@gloggable
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


@gloggable
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
    update.effective_message.reply_text("Successfully promoted {} to whitelist!".format(user_member.user.first_name))
    return "<b>{}:</b>" \
           "\n#WHITELIST" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@gloggable
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


@whitelist_plus
def devlist(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    true_dev = list(set(DEV_USERS))
    msg = "<b>Dev users:</b>\n"
    for each_user in true_dev:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            msg += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    message.reply_text(msg, parse_mode=ParseMode.HTML)


@whitelist_plus
def sudolist(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    true_sudo = list(set(SUDO_USERS))
    msg = "<b>Sudo users:</b>\n"
    for each_user in true_sudo:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            msg += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    message.reply_text(msg, parse_mode=ParseMode.HTML)


@whitelist_plus
def supportlist(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    msg = "<b>Support users:</b>\n"
    for each_user in SUPPORT_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            msg += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    message.reply_text(msg, parse_mode=ParseMode.HTML)


@whitelist_plus
def whitelistlist(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    msg = "<b>Whitelist users:</b>\n"
    for each_user in WHITELIST_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            msg += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    message.reply_text(msg, parse_mode=ParseMode.HTML)


__help__ = """
- /addsudo: adds a user as sudo
- /addsupport: adds a user as support
- /addwhitelist: adds a user as whitelist
- /removesudo: remove a sudo user
- /removesupport: remove support user
- /removewhitelist: remove a whitelist user
- /sudolist: lists all users which have sudo access to the bot
- /supportlist: lists all users which are allowed to gban, but can also be banned
- /whitelistlist: lists all users which cannot be banned, muted flood or kicked but can be manually banned by admins
"""

__mod_name__ = "Super Users"

SUDO_HANDLER = CommandHandler("addsudo", addsudo, pass_args=True, filters=Filters.user(OWNER_ID), run_async=True)
UNSUDO_HANDLER = CommandHandler("removesudo", removesudo, pass_args=True, filters=Filters.user(OWNER_ID), run_async=True)
SUPPORT_HANDLER = CommandHandler("addsupport", addsupport, pass_args=True, filters=Filters.user(OWNER_ID), run_async=True)
UNSUPPORT_HANDLER = CommandHandler("removesupport", removesupport, pass_args=True, filters=Filters.user(OWNER_ID), run_async=True)
WHITELIST_HANDLER = CommandHandler("addwhitelist", addwhitelist, pass_args=True, filters=Filters.user(OWNER_ID), run_async=True)
UNWHITELIST_HANDLER = CommandHandler("removewhitelist", removewhitelist, pass_args=True, filters=Filters.user(OWNER_ID), run_async=True)

DEVLIST_HANDLER = CommandHandler(("devlist"), devlist, run_async=True)
SUDOLIST_HANDLER = CommandHandler(("sudolist"), sudolist, run_async=True)
SUPPORTLIST_HANDLER = CommandHandler(("supportlist"), supportlist, run_async=True)
WHITELISTLIST_HANDLER = CommandHandler(("whitelistlist"), whitelistlist, run_async=True)

dispatcher.add_handler(SUDO_HANDLER)
dispatcher.add_handler(UNSUDO_HANDLER)
dispatcher.add_handler(SUPPORT_HANDLER)
dispatcher.add_handler(UNSUPPORT_HANDLER)
dispatcher.add_handler(WHITELIST_HANDLER)
dispatcher.add_handler(UNWHITELIST_HANDLER)

dispatcher.add_handler(DEVLIST_HANDLER)
dispatcher.add_handler(SUDOLIST_HANDLER)
dispatcher.add_handler(SUPPORTLIST_HANDLER)
dispatcher.add_handler(WHITELISTLIST_HANDLER)
