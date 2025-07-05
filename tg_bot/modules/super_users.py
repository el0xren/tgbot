import html
import json
import os
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, CallbackContext, OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS
from tg_bot.modules.helper_funcs.chat_status import dev_plus, sudo_plus, support_plus, whitelist_plus
from tg_bot.modules.log_channel import gloggable
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.sql import super_users_sql as sql


def check_user_id(user_id: int, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    if not user_id:
        return "Nice try... Nope! Provide me an valid User ID."

    elif user_id == bot.id:
        return "This does not work that way."

    else:
        return None


@dev_plus
@gloggable
def addsudo(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    reply = check_user_id(user_id, bot)

    if not user_id:
        message.reply_text("Invalid user!")
        return ""

    if reply:
        message.reply_text(reply)
        return ""
    if user_id in DEV_USERS:
        message.reply_text("Huh? he is more than sudo!")
        return ""
    if user_id in SUDO_USERS:
        message.reply_text("This member is already sudo")
        return ""
    if user_id in SUPPORT_USERS:
        message.reply_text(
            "This user is already a support user. Promoting to sudo.")
        SUPPORT_USERS.remove(user_id)
    if user_id in WHITELIST_USERS:
        message.reply_text(
            "This user is already a whitelisted user. Promoting to sudo.")
        WHITELIST_USERS.remove(user_id)
    sql.set_superuser_role(user_id, "sudos")
    SUDO_USERS.append(user_id)
    update.effective_message.reply_text(
        "Successfully promoted {} to sudo!".format(
            user_member.user.first_name))
    return "<b>{}:</b>" \
           "\n#SUDO" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@sudo_plus
@gloggable
def addsupport(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    reply = check_user_id(user_id, bot)

    if not user_id:
        message.reply_text("Invalid user!")
        return ""

    if reply:
        message.reply_text(reply)
        return ""
    if user_id in DEV_USERS:
        message.reply_text("Huh? he is more than support!")
        return ""
    if user_id in SUDO_USERS:
        if user.id in DEV_USERS:
            message.reply_text(
                "This member is a sudo user. Demoting to support.")
            SUDO_USERS.remove(user_id)
        else:
            message.reply_text("This user is already sudo")
            return ""
    if user_id in SUPPORT_USERS:
        message.reply_text("This user is already a support user.")
        return ""
    if user_id in WHITELIST_USERS:
        message.reply_text(
            "This user is already a whitelisted user. Promoting to support.")
        WHITELIST_USERS.remove(user_id)
    sql.set_superuser_role(user_id, "supports")
    SUPPORT_USERS.append(user_id)
    update.effective_message.reply_text(
        "Successfully promoted {} to support!".format(
            user_member.user.first_name))
    return "<b>{}:</b>" \
           "\n#SUPPORT" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@sudo_plus
@gloggable
def addwhitelist(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    reply = check_user_id(user_id, bot)

    if not user_id:
        message.reply_text("Invalid user!")
        return ""

    if reply:
        message.reply_text(reply)
        return ""
    if user_id in DEV_USERS:
        message.reply_text("Huh? he is more than whitelist!")
        return ""
    if user_id in SUDO_USERS:
        if user.id in DEV_USERS:
            message.reply_text(
                "This member is a sudo user. Demoting to whitelist.")
            SUDO_USERS.remove(user_id)
        else:
            message.reply_text("This user is already sudo")
            return ""
    if user_id in SUPPORT_USERS:
        message.reply_text(
            "This user is already a support user. Demoting to whitelist.")
        SUPPORT_USERS.remove(user_id)
    if user_id in WHITELIST_USERS:
        message.reply_text("This user is already a whitelisted user.")
        return ""
    sql.set_superuser_role(user_id, "whitelists")
    WHITELIST_USERS.append(user_id)
    update.effective_message.reply_text(
        "Successfully promoted {} to whitelist!".format(
            user_member.user.first_name))
    return "<b>{}:</b>" \
           "\n#WHITELIST" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@dev_plus
@gloggable
def removesudo(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    reply = check_user_id(user_id, bot)

    if not user_id:
        message.reply_text("Invalid user!")
        return ""

    if reply:
        message.reply_text(reply)
        return ""
    if user_id in DEV_USERS:
        message.reply_text("Huh? he is more than sudo!")
        return ""
    if user_id in SUDO_USERS:
        message.reply_text("Demoting to normal user")
        SUDO_USERS.remove(user_id)
        sql.remove_superuser(user_id)
        return "<b>{}:</b>" \
           "\n#UNSUDO" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))
    else:
        message.reply_text("This user is not a sudo!")
        return ""


@sudo_plus
@gloggable
def removesupport(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    reply = check_user_id(user_id, bot)

    if not user_id:
        message.reply_text("Invalid user!")
        return ""

    if reply:
        message.reply_text(reply)
        return ""
    if user_id in SUPPORT_USERS:
        message.reply_text("Demoting to normal user")
        SUPPORT_USERS.remove(user_id)
        sql.remove_superuser(user_id)
        return "<b>{}:</b>" \
           "\n#UNSUPPORT" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))
    else:
        message.reply_text("This user is not a support user!")
        return ""


@sudo_plus
@gloggable
def removewhitelist(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    reply = check_user_id(user_id, bot)

    if not user_id:
        message.reply_text("Invalid user!")
        return ""

    if reply:
        message.reply_text(reply)
        return ""
    if user_id in WHITELIST_USERS:
        message.reply_text("Demoting to normal user")
        WHITELIST_USERS.remove(user_id)
        sql.remove_superuser(user_id)
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
    true_dev = list(set(DEV_USERS) - {OWNER_ID})
    msg = "<b>Dev users:</b>\n"
    for each_user in true_dev:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            if user.first_name == "":
                continue
            msg += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    message.reply_text(msg, parse_mode=ParseMode.HTML)


@whitelist_plus
def sudolist(update: Update, context: CallbackContext) -> None:
    bot: Bot = context.bot
    message = update.effective_message

    true_sudo: List[int] = sorted([user_id for user_id in SUDO_USERS if user_id not in DEV_USERS])

    if not true_sudo:
        message.reply_text("No sudo users found.", parse_mode=ParseMode.HTML)
        return

    msg = "<b>Sudo Users:</b>\n"
    skipped_users = 0

    for user_id in true_sudo:
        try:
            user = bot.get_chat(user_id)
            if not user.first_name:
                skipped_users += 1
                continue
            msg += f"• {mention_html(user_id, html.escape(user.first_name))} (<code>{user_id}</code>)\n"
        except TelegramError:
            skipped_users += 1
            continue

    if not msg.endswith("\n"):
        message.reply_text("No valid sudo users found.", parse_mode=ParseMode.HTML)
        return

    if skipped_users > 0:
        msg += f"\n<i>{skipped_users} user(s) could not be fetched (e.g., deleted accounts or bot blocked).</i>"

    msg += f"\n<b>Total Sudo Users:</b> <code>{len(true_sudo)}</code>"
    message.reply_text(msg, parse_mode=ParseMode.HTML)


@whitelist_plus
def supportlist(update: Update, context: CallbackContext) -> None:
    bot: Bot = context.bot
    message = update.effective_message

    support_users: List[int] = sorted(SUPPORT_USERS)

    if not support_users:
        message.reply_text("No support users found.", parse_mode=ParseMode.HTML)
        return

    msg = "<b>Support Users:</b>\n"
    skipped_users = 0

    for user_id in support_users:
        try:
            user = bot.get_chat(user_id)
            if not user.first_name:
                skipped_users += 1
                continue
            msg += f"• {mention_html(user_id, html.escape(user.first_name))} (<code>{user_id}</code>)\n"
        except TelegramError:
            skipped_users += 1
            continue

    if not msg.endswith("\n"):
        message.reply_text("No valid support users found.", parse_mode=ParseMode.HTML)
        return

    if skipped_users > 0:
        msg += f"\n<i>{skipped_users} user(s) could not be fetched (e.g., deleted accounts or bot blocked).</i>"

    msg += f"\n<b>Total Support Users:</b> <code>{len(support_users)}</code>"
    message.reply_text(msg, parse_mode=ParseMode.HTML)


@whitelist_plus
def whitelistlist(update: Update, context: CallbackContext) -> None:
    bot: Bot = context.bot
    message = update.effective_message

    whitelist_users: List[int] = sorted(WHITELIST_USERS)

    if not whitelist_users:
        message.reply_text("No whitelist users found.", parse_mode=ParseMode.HTML)
        return

    msg = "<b>Whitelist Users:</b>\n"
    skipped_users = 0

    for user_id in whitelist_users:
        try:
            user = bot.get_chat(user_id)
            if not user.first_name:
                skipped_users += 1
                continue
            msg += f"• {mention_html(user_id, html.escape(user.first_name))} (<code>{user_id}</code>)\n"
        except TelegramError:
            skipped_users += 1
            continue

    if not msg.endswith("\n"):
        message.reply_text("No valid whitelist users found.", parse_mode=ParseMode.HTML)
        return

    if skipped_users > 0:
        msg += f"\n<i>{skipped_users} user(s) could not be fetched (e.g., deleted accounts or bot blocked).</i>"

    msg += f"\n<b>Total Whitelist Users:</b> <code>{len(whitelist_users)}</code>"
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

SUDO_HANDLER = CommandHandler("addsudo", addsudo, run_async=True)
UNSUDO_HANDLER = CommandHandler("removesudo", removesudo, run_async=True)
SUPPORT_HANDLER = CommandHandler("addsupport", addsupport, run_async=True)
UNSUPPORT_HANDLER = CommandHandler("removesupport",
                                   removesupport,
                                   run_async=True)
WHITELIST_HANDLER = CommandHandler("addwhitelist",
                                   addwhitelist,
                                   run_async=True)
UNWHITELIST_HANDLER = CommandHandler("removewhitelist",
                                     removewhitelist,
                                     run_async=True)
DEVLIST_HANDLER = CommandHandler(("devlist"), devlist, run_async=True)
SUDOLIST_HANDLER = CommandHandler(("sudolist"), sudolist, run_async=True)
SUPPORTLIST_HANDLER = CommandHandler(("supportlist"),
                                     supportlist,
                                     run_async=True)
WHITELISTLIST_HANDLER = CommandHandler(("whitelistlist"),
                                       whitelistlist,
                                       run_async=True)

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
