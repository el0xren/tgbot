<<<<<<< HEAD
import html
import re
from typing import Optional, List

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery
from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, DispatcherHandlerStop, MessageHandler, Filters, CallbackQueryHandler
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, CallbackContext, BAN_STICKER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import is_user_admin, bot_admin, user_admin_no_reply, user_admin, \
    can_restrict, can_delete
from tg_bot.modules.helper_funcs.extraction import extract_text, extract_user_and_text, extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import split_message
from tg_bot.modules.helper_funcs.string_handling import split_quotes
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import warns_sql as sql
from tg_bot.modules.sql.approve_sql import is_approved

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = "<b>Current warning filters in this chat:</b>\n"


# Not async
def warn(user: User,
         chat: Chat,
         reason: str,
         message: Message,
         warner: User = None) -> str:
    if is_user_admin(chat, user.id):
        message.reply_text("Damn admins, can't even be warned!")
        return ""

    if not user.id or int(user.id) == 777000 or int(user.id) == 1087968824:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = "{} warnings, {} has been kicked!".format(
                limit, mention_html(user.id, user.first_name))

        else:  # ban
            chat.ban_member(user.id)
            reply = "{} warnings, {} has been banned!".format(
                limit, mention_html(user.id, user.first_name))

        for warn_reason in reasons:
            reply += "\n - {}".format(html.escape(warn_reason))

        message.bot.send_sticker(chat.id,
                                 BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        log_reason = "<b>{}:</b>" \
                     "\n#WARN_BAN" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {} (<code>{}</code>)" \
                     "\n<b>Reason:</b> {}"\
                     "\n<b>Counts:</b> <code>{}/{}</code>".format(html.escape(chat.title),
                                                                  warner_tag,
                                                                  mention_html(user.id, user.first_name),
                                                                  user.id, reason, num_warns, limit)

    else:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Remove warn",
                                 callback_data="rm_warn({})".format(user.id))
        ]])

        reply = "{} has {}/{} warnings... watch out!".format(
            mention_html(user.id, user.first_name), num_warns, limit)
        if reason:
            reply += "\nReason for last warn:\n{}".format(html.escape(reason))

        log_reason = "<b>{}:</b>" \
                     "\n#WARN" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {} (<code>{}</code>)" \
                     "\n<b>Reason:</b> {}"\
                     "\n<b>Counts:</b> <code>{}/{}</code>".format(html.escape(chat.title),
                                                                  warner_tag,
                                                                  mention_html(user.id, user.first_name),
                                                                  user.id, reason, num_warns, limit)

    try:
        message.reply_text(reply,
                           reply_markup=keyboard,
                           parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(reply,
                               reply_markup=keyboard,
                               parse_mode=ParseMode.HTML,
                               quote=False)
        else:
            raise
    return log_reason


def swarn(user: User,
          chat: Chat,
          reason: str,
          message: Message,
          warner: User = None) -> str:
    if is_user_admin(chat, user.id):
        message.reply_text("Damn admins, can't even be warned!")
        return ""

    if not user.id or int(user.id) == 777000 or int(user.id) == 1087968824:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = "{} warnings, {} has been kicked!".format(
                limit, mention_html(user.id, user.first_name))

        else:  # ban
            chat.ban_member(user.id)
            reply = "{} warnings, {} has been banned!".format(
                limit, mention_html(user.id, user.first_name))

        for warn_reason in reasons:
            reply += "\n - {}".format(html.escape(warn_reason))

        message.bot.send_sticker(chat.id,
                                 BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        log_reason = "<b>{}:</b>" \
                     "\n#WARN_BAN" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {} (<code>{}</code>)" \
                     "\n<b>Reason:</b> {}"\
                     "\n<b>Counts:</b> <code>{}/{}</code>".format(html.escape(chat.title),
                                                                  warner_tag,
                                                                  mention_html(user.id, user.first_name),
                                                                  user.id, reason, num_warns, limit)

    else:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Remove warn",
                                 callback_data="rm_warn({})".format(user.id))
        ]])

        reply = "{} has {}/{} warnings... watch out!".format(
            mention_html(user.id, user.first_name), num_warns, limit)
        if reason:
            reply += "\nReason for last warn:\n{}".format(html.escape(reason))

        log_reason = "<b>{}:</b>" \
                     "\n#WARN" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {} (<code>{}</code>)" \
                     "\n<b>Reason:</b> {}"\
                     "\n<b>Counts:</b> <code>{}/{}</code>".format(html.escape(chat.title),
                                                                  warner_tag,
                                                                  mention_html(user.id, user.first_name),
                                                                  user.id, reason, num_warns, limit)

    try:
        if message.reply_to_message:
            message.reply_to_message.delete()
        message.reply_text(reply,
                           reply_markup=keyboard,
                           parse_mode=ParseMode.HTML)
        message.delete()
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            if message.reply_to_message:
                message.reply_to_message.delete()
            message.reply_text(reply,
                               reply_markup=keyboard,
                               parse_mode=ParseMode.HTML,
                               quote=False)
            message.delete()
        else:
            raise
    return log_reason


def dwarn(user: User,
          chat: Chat,
          reason: str,
          message: Message,
          warner: User = None) -> str:
    if is_user_admin(chat, user.id):
        message.reply_text("Damn admins, can't even be warned!")
        return ""

    if not user.id or int(user.id) == 777000 or int(user.id) == 1087968824:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = "{} warnings, {} has been kicked!".format(
                limit, mention_html(user.id, user.first_name))

        else:  # ban
            chat.ban_member(user.id)
            reply = "{} warnings, {} has been banned!".format(
                limit, mention_html(user.id, user.first_name))

        for warn_reason in reasons:
            reply += "\n - {}".format(html.escape(warn_reason))

        message.bot.send_sticker(chat.id,
                                 BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        log_reason = "<b>{}:</b>" \
                     "\n#WARN_BAN" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {} (<code>{}</code>)" \
                     "\n<b>Reason:</b> {}"\
                     "\n<b>Counts:</b> <code>{}/{}</code>".format(html.escape(chat.title),
                                                                  warner_tag,
                                                                  mention_html(user.id, user.first_name),
                                                                  user.id, reason, num_warns, limit)

    else:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Remove warn",
                                 callback_data="rm_warn({})".format(user.id))
        ]])

        reply = "{} has {}/{} warnings... watch out!".format(
            mention_html(user.id, user.first_name), num_warns, limit)
        if reason:
            reply += "\nReason for last warn:\n{}".format(html.escape(reason))

        log_reason = "<b>{}:</b>" \
                     "\n#WARN" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {} (<code>{}</code>)" \
                     "\n<b>Reason:</b> {}"\
                     "\n<b>Counts:</b> <code>{}/{}</code>".format(html.escape(chat.title),
                                                                  warner_tag,
                                                                  mention_html(user.id, user.first_name),
                                                                  user.id, reason, num_warns, limit)

    try:
        if message.reply_to_message:
            message.reply_to_message.delete()
        message.reply_text(reply,
                           reply_markup=keyboard,
                           parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            if message.reply_to_message:
                message.reply_to_message.delete()
            message.reply_text(reply,
                               reply_markup=keyboard,
                               parse_mode=ParseMode.HTML,
                               quote=False)
        else:
            raise
    return log_reason


@bot_admin
@loggable
def button(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    query = update.callback_query  # type: Optional[CallbackQuery]
    user = update.effective_user  # type: Optional[User]
    match = re.match(r"rm_warn\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat = update.effective_chat  # type: Optional[Chat]
        if not is_user_admin(chat, int(user.id)):
            query.answer(text="Who dis non-admin telling me what to do?",
                         show_alert=True)
            return ""
        res = sql.remove_warn(user_id, chat.id)
        if res:
            update.effective_message.edit_text("Warn removed by {}.".format(
                mention_html(user.id, user.first_name)),
                                               parse_mode=ParseMode.HTML)
            user_member = chat.get_member(user_id)
            return "<b>{}:</b>" \
                   "\n#UNWARN" \
                   "\n<b>Admin:</b> {}" \
                   "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                                mention_html(user.id, user.first_name),
                                                                mention_html(user_member.user.id, user_member.user.first_name),
                                                                user_member.user.id)
        else:
            update.effective_message.edit_text(
                "User has already has no warns.".format(
                    mention_html(user.id, user.first_name)),
                parse_mode=ParseMode.HTML)

    return ""


@user_admin
@bot_admin
@loggable
def remove_warns(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)

    if user_id:
        sql.remove_warn(user_id, chat.id)
        message.reply_text("Last warn has been removed!")
        warned = chat.get_member(user_id).user
        return "<b>{}:</b>" \
               "\n#UNWARN" \
               "\n<b>Admin:</b> {}" \
               "\n<b>User:</b> {}" \
               "\n<b>ID:</b> (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(warned.id, warned.first_name),
                                                       warned.id)
    else:
        message.reply_text("No user has been designated!")
    return ""


@user_admin
@can_restrict
@loggable
def warn_user(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    warner = update.effective_user  # type: Optional[User]

    user_id, reason = extract_user_and_text(message, args)
    if message.text.startswith('/s'):
        silent = True
        if not can_delete(chat, context.bot.id):
            return ""
    else:
        silent = False
    if message.text.startswith('/d'):
        delban = True
        if not can_delete(chat, context.bot.id):
            return ""
    else:
        delban = False
    if silent:
        if user_id:
            if message.reply_to_message and message.reply_to_message.from_user.id == user_id:
                return swarn(message.reply_to_message.from_user, chat, reason,
                             message, warner)
            else:
                return swarn(
                    chat.get_member(user_id).user, chat, reason, message,
                    warner)
        else:
            message.reply_text("That looks like an invalid User ID to me.")
    elif delban:
        if user_id:
            if message.reply_to_message and message.reply_to_message.from_user.id == user_id:
                return dwarn(message.reply_to_message.from_user, chat, reason,
                             message, warner)
            else:
                return dwarn(
                    chat.get_member(user_id).user, chat, reason, message,
                    warner)
        else:
            message.reply_text("That looks like an invalid User ID to me.")
    else:
        if user_id:
            if message.reply_to_message and message.reply_to_message.from_user.id == user_id:
                return warn(message.reply_to_message.from_user, chat, reason,
                            message.reply_to_message, warner)
            else:
                return warn(
                    chat.get_member(user_id).user, chat, reason, message,
                    warner)
        else:
            message.reply_text("No user was designated!")
        return ""


@user_admin
@bot_admin
@loggable
def reset_warns(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)

    if user_id:
        sql.reset_warns(user_id, chat.id)
        message.reply_text("Warnings have been reset!")
        warned = chat.get_member(user_id).user
        return "<b>{}:</b>" \
               "\n#RESETWARNS" \
               "\n<b>Admin:</b> {}" \
               "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                            mention_html(user.id, user.first_name),
                                                            mention_html(warned.id, warned.first_name),
                                                            warned.id)
    else:
        message.reply_text("No user has been designated!")
    return ""


def warns(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user_id = extract_user(message, args) or update.effective_user.id
    result = sql.get_warns(user_id, chat.id)

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn = sql.get_warn_setting(chat.id)

        if reasons:
            text = "This user has {}/{} warnings, for the following reasons:".format(
                num_warns, limit)
            for reason in reasons:
                text += "\n - {}".format(reason)

            msgs = split_message(text)
            for msg in msgs:
                update.effective_message.reply_text(msg)
        else:
            update.effective_message.reply_text(
                "User has {}/{} warnings, but no reasons for any of them.".
                format(num_warns, limit))
    else:
        update.effective_message.reply_text(
            "This user hasn't got any warnings!")


# Dispatcher handler stop - do not async
@user_admin
def add_warn_filter(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    args = msg.text.split(
        None,
        1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) >= 2:
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()
        content = extracted[1]

    else:
        return

    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(WARN_HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, WARN_HANDLER_GROUP)

    sql.add_warn_filter(chat.id, keyword, content)

    update.effective_message.reply_text(
        "Warn handler added for '{}'!".format(keyword))
    raise DispatcherHandlerStop


@user_admin
def remove_warn_filter(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    args = msg.text.split(
        None,
        1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 1:
        return

    to_remove = extracted[0]

    chat_filters = sql.get_chat_warn_triggers(chat.id)

    if not chat_filters:
        msg.reply_text("No warning filters are active here!")
        return

    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat.id, to_remove)
            msg.reply_text("Yep, I'll stop warning people for that.")
            raise DispatcherHandlerStop

    msg.reply_text(
        "That's not a current warning filter - run /warnlist for all active warning filters."
    )


def list_warn_filters(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    all_handlers = sql.get_chat_warn_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text(
            "No warning filters are active here!")
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = " - {}\n".format(html.escape(keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(filter_list,
                                                parse_mode=ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == CURRENT_WARNING_FILTER_STRING:
        update.effective_message.reply_text(filter_list,
                                            parse_mode=ParseMode.HTML)


@loggable
def reply_filter(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user

    if is_approved(chat.id, user.id):
        return

    chat_warn_filters = sql.get_chat_warn_triggers(chat.id)
    to_match = extract_text(message)
    if not to_match:
        return ""

    for keyword in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            user = update.effective_user  # type: Optional[User]
            warn_filter = sql.get_warn_filter(chat.id, keyword)
            return warn(user, chat, warn_filter.reply, message)
    return ""


@user_admin
@loggable
def set_warn_limit(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    if args:
        if args[0].isdigit():
            if int(args[0]) < 3:
                msg.reply_text("The minimum warn limit is 3!")
            else:
                sql.set_warn_limit(chat.id, int(args[0]))
                msg.reply_text("Updated the warn limit to {}".format(args[0]))
                return "<b>{}:</b>" \
                       "\n#SET_WARN_LIMIT" \
                       "\n<b>Admin:</b> {}" \
                       "\nSet the warn limit to <code>{}</code>".format(html.escape(chat.title),
                                                                        mention_html(user.id, user.first_name), args[0])
        else:
            msg.reply_text("Give me a number as an arg!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)

        msg.reply_text("The current warn limit is {}".format(limit))
    return ""


@user_admin
def set_warn_strength(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    if args:
        if args[0].lower() in ("on", "yes"):
            sql.set_warn_strength(chat.id, False)
            msg.reply_text("Too many warns will now result in a ban!")
            return "<b>{}:</b>\n" \
                   "<b>Admin:</b> {}\n" \
                   "Has enabled strong warns. Users will be banned.".format(html.escape(chat.title),
                                                                            mention_html(user.id, user.first_name))

        elif args[0].lower() in ("off", "no"):
            sql.set_warn_strength(chat.id, True)
            msg.reply_text(
                "Too many warns will now result in a kick! Users will be able to join again after."
            )
            return "<b>{}:</b>\n" \
                   "<b>Admin:</b> {}\n" \
                   "Has disabled strong warns. Users will only be kicked.".format(html.escape(chat.title),
                                                                                  mention_html(user.id,
                                                                                               user.first_name))

        else:
            msg.reply_text("I only understand on/yes/no/off!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)
        if soft_warn:
            msg.reply_text(
                "Warns are currently set to *kick* users when they exceed the limits.",
                parse_mode=ParseMode.MARKDOWN)
        else:
            msg.reply_text(
                "Warns are currently set to *ban* users when they exceed the limits.",
                parse_mode=ParseMode.MARKDOWN)
    return ""


def __stats__():
    return "{} overall warns, across {} chats.\n" \
           "{} warn filters, across {} chats.".format(sql.num_warns(), sql.num_warn_chats(),
                                                      sql.num_warn_filters(), sql.num_warn_filter_chats())


def __import_data__(chat_id, data):
    for user_id, count in data.get('warns', {}).items():
        for x in range(int(count)):
            sql.warn_user(user_id, chat_id)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    num_warn_filters = sql.num_warn_chat_filters(chat_id)
    limit, soft_warn = sql.get_warn_setting(chat_id)
    return "This chat has `{}` warn filters. It takes `{}` warns " \
           "before the user gets *{}*.".format(num_warn_filters, limit, "kicked" if soft_warn else "banned")


__help__ = """
 - /warns <userhandle>: get a user's number, and reason, of warnings.
 - /warnlist: list of all current warning filters

*Admin only:*
 - /warn <userhandle>: warn a user. After 3 warns, the user will be banned from the group. Can also be used as a reply.
 - /swarn <userhandle>: warns a user silently.
 - /dwarn <userhandle>: warns a user and deletes the message which is replied to.
 - /resetwarn <userhandle>: reset the warnings for a user. Can also be used as a reply.
 - /addwarn <keyword> <reply message>: set a warning filter on a certain keyword. If you want your keyword to \
be a sentence, encompass it with quotes, as such: `/addwarn "very angry" This is an angry user`. 
 - /nowarn <keyword>: stop a warning filter
 - /warnlimit <num>: set the warning limit
 - /strongwarn <on/yes/off/no>: If set to on, exceeding the warn limit will result in a ban. Else, will just kick.
 - /rmwarn <userhandle>: removes latest warn for a user. It also can be used as reply.
 - /unwarn <userhandle>: same as /rmwarn
"""

__mod_name__ = "Warnings"

WARN_HANDLER = CommandHandler("warn",
                              warn_user,
                              run_async=True,
                              filters=Filters.chat_type.groups)
SWARN_HANDLER = CommandHandler("swarn",
                               warn_user,
                               run_async=True,
                               filters=Filters.chat_type.groups)
DWARN_HANDLER = CommandHandler("dwarn",
                               warn_user,
                               run_async=True,
                               filters=Filters.chat_type.groups)
RESET_WARN_HANDLER = CommandHandler(["resetwarn", "resetwarns"],
                                    reset_warns,
                                    run_async=True,
                                    filters=Filters.chat_type.groups)
CALLBACK_QUERY_HANDLER = CallbackQueryHandler(button, pattern=r"rm_warn")
MYWARNS_HANDLER = DisableAbleCommandHandler("warns",
                                            warns,
                                            run_async=True,
                                            filters=Filters.chat_type.groups)
ADD_WARN_HANDLER = CommandHandler("addwarn",
                                  add_warn_filter,
                                  filters=Filters.chat_type.groups)
RM_WARN_HANDLER = CommandHandler(["nowarn", "stopwarn"],
                                 remove_warn_filter,
                                 filters=Filters.chat_type.groups)
LIST_WARN_HANDLER = DisableAbleCommandHandler(["warnlist", "warnfilters"],
                                              list_warn_filters,
                                              filters=Filters.chat_type.groups,
                                              admin_ok=True)
WARN_FILTER_HANDLER = MessageHandler(
    CustomFilters.has_text & Filters.chat_type.groups, reply_filter)
WARN_LIMIT_HANDLER = CommandHandler("warnlimit",
                                    set_warn_limit,
                                    run_async=True,
                                    filters=Filters.chat_type.groups)
WARN_STRENGTH_HANDLER = CommandHandler("strongwarn",
                                       set_warn_strength,
                                       run_async=True,
                                       filters=Filters.chat_type.groups)
REMOVE_WARNS_HANDLER = CommandHandler(["rmwarn", "unwarn"],
                                      remove_warns,
                                      run_async=True,
                                      filters=Filters.chat_type.groups)

dispatcher.add_handler(WARN_HANDLER)
dispatcher.add_handler(SWARN_HANDLER)
dispatcher.add_handler(DWARN_HANDLER)
dispatcher.add_handler(CALLBACK_QUERY_HANDLER)
dispatcher.add_handler(RESET_WARN_HANDLER)
dispatcher.add_handler(MYWARNS_HANDLER)
dispatcher.add_handler(ADD_WARN_HANDLER)
dispatcher.add_handler(RM_WARN_HANDLER)
dispatcher.add_handler(LIST_WARN_HANDLER)
dispatcher.add_handler(WARN_LIMIT_HANDLER)
dispatcher.add_handler(WARN_STRENGTH_HANDLER)
dispatcher.add_handler(WARN_FILTER_HANDLER, WARN_HANDLER_GROUP)
dispatcher.add_handler(REMOVE_WARNS_HANDLER)
=======
import html
import re
from typing import Optional
from sqlalchemy.sql.expression import false

import telegram
from tg_bot import BAN_STICKER, DEV_USERS, OWNER_ID, SUDO_USERS, WHITELIST_USERS, dispatcher, spamcheck
#from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    is_user_admin,
    user_admin,
    can_delete,
    user_admin_no_reply,
    user_mod,
)
from tg_bot.modules.helper_funcs.extraction import (
    extract_text,
    extract_user,
    extract_user_and_text,
)
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import split_message
from tg_bot.modules.helper_funcs.string_handling import split_quotes
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import warns_sql as sql
from tg_bot.modules.sql.approve_sql import is_approved
from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    Update,
    User,
)
from telegram.error import BadRequest
from telegram.ext import (
    CallbackContext,
    DispatcherHandlerStop,
    Filters,
)
from telegram.utils.helpers import mention_html
from tg_bot.modules.helper_funcs.decorators import kigcmd, kigmsg, kigcallback

from ..modules.helper_funcs.anonymous import user_admin as u_admin, AdminPerms, resolve_user as res_user, UserClass

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = "<b>Current warning filters in this chat:</b>\n"
WARNS_GROUP = 2

def warn_immune(message, update, uid, warner):

    if is_user_admin(update, uid):
        if uid is OWNER_ID:
            message.reply_text("This is my CREATOR, how dare you!")
            return True
        if uid in DEV_USERS:
            message.reply_text("This user is one of my Devs, go cry somewhere else.")
            return True
        if uid in SUDO_USERS:
            message.reply_text("This user is a SUDO user, i'm not gonna warn him!")
            return True
        else:
            message.reply_text("Damn admins, They are too far to be warned!")
            return True

    if uid in WHITELIST_USERS:
        if warner:
            message.reply_text("Whitelisted users are warn immune.")
            return True
        else:
            message.reply_text(
                "A whitelisted user triggered an auto warn filter!\nI can't warn them users but they should avoid abusing this."
            )
            return True
    else:
        return False

# Not async
def warn(
    user: User, update: Update, reason: str, message: Message, warner: User = None
) -> Optional[str]:  # sourcery no-metrics
    chat = update.effective_chat
    if warn_immune(message=message, update=update, uid=user.id, warner=warner):
        return

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = (
                f"<code>❕</code><b>Kick Event</b>\n"
                f"<code> </code><b>•  User:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  Count:</b> {limit}"
            )

        else:  # ban
            chat.ban_member(user.id)
            reply = (
                f"<code>❕</code><b>Ban Event</b>\n"
                f"<code> </code><b>•  User:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  Count:</b> {limit}"
            )

        for warn_reason in reasons:
            reply += f"\n - {html.escape(warn_reason)}"

        message.bot.send_sticker(chat.id, BAN_STICKER)  # Saitama's sticker
        keyboard = None
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN_BAN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit}</code>"
        )

    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔘 Remove warn", callback_data="rm_warn({})".format(user.id)
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📝 Read the rules", url="t.me/{}?start={}".format(dispatcher.bot.username, chat.id)
                    )
                ],
            ]
        )

        reply = (
            f"<code>❕</code><b>Warn Event</b>\n"
            f"<code> </code><b>•  User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<code> </code><b>•  Count:</b> {num_warns}/{limit}\n"
        )
        if reason:
            reply += f"\n<code> </code><b>•  Reason:</b> {html.escape(reason)}"
        reply += '\nPlease take some of your precious time to read the rules!'

        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit}</code>"
        )

    try:
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, quote=False
            )
        else:
            raise
    return log_reason

# Not async
def swarn(
    user: User, update: Update, reason: str, message: Message, dels, warner: User = None,
) -> str:  # sourcery no-metrics
    if warn_immune(message=message, update=update, uid=user.id, warner=warner):
        return
    chat = update.effective_chat

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = (
                f"<code>❕</code><b>Kick Event</b>\n"
                f"<code> </code><b>•  User:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  Count:</b> {limit}"
            )

        else:  # ban
            chat.ban_member(user.id)
            reply = (
                f"<code>❕</code><b>Ban Event</b>\n"
                f"<code> </code><b>•  User:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  Count:</b> {limit}"
            )

        for warn_reason in reasons:
            reply += f"\n - {html.escape(warn_reason)}"

        message.bot.send_sticker(chat.id, BAN_STICKER)  # Saitama's sticker
        keyboard = None
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN_BAN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User ID:</b> <code>{user.id}</code>\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit}</code>"
        )

    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔘 Remove warn", callback_data="rm_warn({})".format(user.id)
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📝 Read the rules", url="t.me/{}?start={}".format(dispatcher.bot.username, chat.id)
                    )
                ],
            ]
        )

        reply = (
            f"<code>❕</code><b>Warn Event</b>\n"
            f"<code> </code><b>•  User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<code> </code><b>•  Count:</b> {num_warns}/{limit}\n"

        )
        if reason:
            reply += f"\n<code> </code><b>•  Reason:</b> {html.escape(reason)}"

        reply += f"\nPlease take some of your precious time to read the rules!"

        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User ID:</b> <code>{user.id}</code>\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit}</code>"
        )

    try:
        if dels:
            if message.reply_to_message:
                message.reply_to_message.delete()
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        message.delete()
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            if message.reply_to_message:
                message.reply_to_message.delete()
            message.reply_text(
                reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, quote=False
            )
            message.delete()
        else:
            raise
    return log_reason

# Not async
def dwarn(
    user: User, update: Update, reason: str, message: Message, warner: User = None
) -> str:  # sourcery no-metrics
    if warn_immune(message=message, update=update, uid=user.id, warner=warner):
        return
    chat = update.effective_chat
    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = (
                f"<code>❕</code><b>Kick Event</b>\n"
                f"<code> </code><b>•  User:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  Count:</b> {limit}"
            )

        else:  # ban
            chat.ban_member(user.id)
            reply = (
                f"<code>❕</code><b>Ban Event</b>\n"
                f"<code> </code><b>•  User:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  Count:</b> {limit}"
            )

        for warn_reason in reasons:
            reply += f"\n - {html.escape(warn_reason)}"

        message.bot.send_sticker(chat.id, BAN_STICKER)  # Saitama's sticker
        keyboard = None
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN_BAN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit}</code>"
        )

    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔘 Remove warn", callback_data="rm_warn({})".format(user.id)
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📝 Read the rules", url="t.me/{}?start={}".format(dispatcher.bot.username, chat.id)
                    )
                ],
            ]
        )

        reply = (
            f"<code>❕</code><b>Warn Event</b>\n"
            f"<code> </code><b>•  User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<code> </code><b>•  Count:</b> {num_warns}/{limit}\n"

        )
        if reason:
            reply += f"\n<code> </code><b>•  Reason:</b> {html.escape(reason)}"
        reply += f"\nPlease take some of your precious time to read the rules!"
        
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit}</code>"
        )

    try:
        if message.reply_to_message:
            message.reply_to_message.delete()
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            if message.reply_to_message:
                message.reply_to_message.delete()
            message.reply_text(
                reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, quote=False
            )
        else:
            raise
    return log_reason

@kigcallback(pattern=r"rm_warn")
@user_admin_no_reply
@bot_admin
@loggable
def button(update: Update, context: CallbackContext) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    match = re.match(r"rm_warn\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        res = sql.remove_warn(user_id, chat.id)
        if res:
            update.effective_message.edit_text(
                "Warn removed by {}.".format(mention_html(user.id, user.first_name)),
                parse_mode=ParseMode.HTML,
            )
            user_member = chat.get_member(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNWARN\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}\n"
                f"<b>User ID:</b> <code>{user_member.user.id}</code>"
                
            )
        else:
            update.effective_message.edit_text(
                "User already has no warns.", parse_mode=ParseMode.HTML
            )

    return ""

@kigcmd(command='swarn', filters=Filters.chat_type.groups)
@kigcmd(command='dwarn', filters=Filters.chat_type.groups)
@kigcmd(command='dswarn', filters=Filters.chat_type.groups)
@kigcmd(command='warn', filters=Filters.chat_type.groups)
@spamcheck
@can_restrict
@u_admin(UserClass.MOD, AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
def warn_user(update: Update, context: CallbackContext) -> str:
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    u: Optional[User] = update.effective_user
    warner = res_user(u, message.message_id, chat)

    user_id, reason = extract_user_and_text(message, args)
    if message.text.startswith('/s') or message.text.startswith('!s') or message.text.startswith('>s'):
        silent = True
        if not can_delete(chat, context.bot.id):
            return ""
    else:
        silent = False
    if message.text.startswith('/d') or message.text.startswith('!d') or message.text.startswith('>d'):
        delban = True
        if not can_delete(chat, context.bot.id):
            return ""
    else:
        delban = False
    if message.text.startswith('/ds') or message.text.startswith('!ds') or message.text.startswith('>ds'):
        delsilent = True
        if not can_delete(chat, context.bot.id):
            return ""
    else:
        delsilent = False
    if silent:
        dels = False
        if user_id:
            if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
            ):
                return swarn(
                    message.reply_to_message.from_user,
                    update,
                    reason,
                    message,
                    dels,
                    warner,
                )
            else:
                return swarn(chat.get_member(user_id).user, update, reason, message, dels, warner)
        else:
            message.reply_text("That looks like an invalid User ID to me.")
    if delsilent:
        dels = True
        if user_id:
            if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
            ):
                return swarn(
                    message.reply_to_message.from_user,
                    update,
                    reason,
                    message,
                    dels,
                    warner,
                )
            else:
                return swarn(chat.get_member(user_id).user, update, reason, message, dels, warner)
        else:
            message.reply_text("That looks like an invalid User ID to me.")
    elif delban:
        if user_id:
            if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
            ):
                return dwarn(
                    message.reply_to_message.from_user,
                    update,
                    reason,
                    message,
                    warner,
                )
            else:
                return dwarn(chat.get_member(user_id).user, update, reason, message, warner)
        else:
            message.reply_text("That looks like an invalid User ID to me.")
    else:
        if user_id:
            if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
            ):
                return warn(
                    message.reply_to_message.from_user,
                    update,
                    reason,
                    message.reply_to_message,
                    warner,
                )
            else:
                return warn(chat.get_member(user_id).user, update, reason, message, warner)
        else:
            message.reply_text("That looks like an invalid User ID to me.")
    return ""

@kigcmd(command=['restwarn', 'resetwarns'], filters=Filters.chat_type.groups)
@spamcheck
@bot_admin
@u_admin(UserClass.ADMIN, AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
def reset_warns(update: Update, context: CallbackContext) -> str:
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    u: Optional[User] = update.effective_user
    user = res_user(u, message.message_id, chat)

    user_id = extract_user(message, args)

    if user_id:
        sql.reset_warns(user_id, chat.id)
        message.reply_text("Warns have been reset!")
        warned = chat.get_member(user_id).user
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#RESETWARNS\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(warned.id, warned.first_name)}\n"
            f"<b>User ID:</b> <code>{warned.id}</code>"
        )
    else:
        message.reply_text("No user has been designated!")
    return ""

@kigcmd(command='warns', filters=Filters.chat_type.groups, can_disable=True)
@spamcheck
def warns(update: Update, context: CallbackContext):
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    user_id = extract_user(message, args) or update.effective_user.id
    result = sql.get_warns(user_id, chat.id)

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn = sql.get_warn_setting(chat.id)

        if reasons:
            text = (
                f"This user has {num_warns}/{limit} warns, for the following reasons:"
            )
            for reason in reasons:
                text += f"\n • {reason}"

            msgs = split_message(text)
            for msg in msgs:
                update.effective_message.reply_text(msg)
        else:
            update.effective_message.reply_text(
                f"User has {num_warns}/{limit} warns, but no reasons for any of them."
            )
    else:
        update.effective_message.reply_text("This user doesn't have any warns!")

@kigcmd(command='addwarn', filters=Filters.chat_type.groups, run_async=False)
@spamcheck
# Dispatcher handler stop - do not async
@u_admin(UserClass.MOD, AdminPerms.CAN_CHANGE_INFO)
def add_warn_filter(update: Update, context: CallbackContext):
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message
    u = update.effective_user
    user = res_user(u, msg.message_id, chat)

    args = msg.text.split(
        None, 1
    )  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 2:
        return

    # set trigger -> lower, so as to avoid adding duplicate filters with different cases
    keyword = extracted[0].lower()
    content = extracted[1]

    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(WARN_HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, WARN_HANDLER_GROUP)

    sql.add_warn_filter(chat.id, keyword, content)

    update.effective_message.reply_text(f"Warn handler added for '{keyword}'!")
    raise DispatcherHandlerStop

@kigcmd(command=['nowarn', 'stopwarn'], filters=Filters.chat_type.groups)
@spamcheck
@u_admin(UserClass.ADMIN, AdminPerms.CAN_CHANGE_INFO)
def remove_warn_filter(update: Update, context: CallbackContext):
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message
    u = update.effective_user
    user = res_user(u, msg.message_id, chat)

    args = msg.text.split(
        None, 1
    )  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 1:
        return

    to_remove = extracted[0]

    chat_filters = sql.get_chat_warn_triggers(chat.id)

    if not chat_filters:
        msg.reply_text("No warning filters are active here!")
        return

    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat.id, to_remove)
            msg.reply_text("Okay, I'll stop warning people for that.")
            raise DispatcherHandlerStop

    msg.reply_text(
        "That's not a current warning filter - run /warnlist for all active warning filters."
    )

@kigcmd(command=['warnlist', 'warnfilters'], filters=Filters.chat_type.groups, can_disable=True)
@spamcheck
def list_warn_filters(update: Update, context: CallbackContext):
    chat: Optional[Chat] = update.effective_chat
    all_handlers = sql.get_chat_warn_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text("No warning filters are active here!")
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = f" - {html.escape(keyword)}\n"
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if filter_list != CURRENT_WARNING_FILTER_STRING:
        update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)

@kigmsg((CustomFilters.has_text & Filters.chat_type.groups), group=WARNS_GROUP)
@loggable
def reply_filter(update: Update, context: CallbackContext) -> Optional[str]:
    chat: Optional[Chat] = update.effective_chat
    message: Optional[Message] = update.effective_message
    user: Optional[User] = update.effective_user

    if not user:  # Ignore channel
        return

    if user.id == 777000:
        return
    if is_approved(chat.id, user.id):
        return

    chat_warn_filters = sql.get_chat_warn_triggers(chat.id)
    to_match = extract_text(message)
    if not to_match:
        return ""

    for keyword in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            user: Optional[User] = update.effective_user
            warn_filter = sql.get_warn_filter(chat.id, keyword)
            return warn(user, update, warn_filter.reply, message)
    return ""

@kigcmd(command='warnlimit', filters=Filters.chat_type.groups)
@spamcheck
@u_admin(UserClass.ADMIN, AdminPerms.CAN_CHANGE_INFO)
@loggable
def set_warn_limit(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat: Optional[Chat] = update.effective_chat
    u: Optional[User] = update.effective_user
    msg: Optional[Message] = update.effective_message
    user = res_user(u, msg.message_id, chat)

    if args:
        if args[0].isdigit():
            if int(args[0]) < 3:
                msg.reply_text("The minimum warn limit is 3!")
            else:
                sql.set_warn_limit(chat.id, int(args[0]))
                msg.reply_text("Updated the warn limit to {}".format(args[0]))
                return (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#SET_WARN_LIMIT\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                    f"Set the warn limit to <code>{args[0]}</code>"
                )
        else:
            msg.reply_text("Give me a number as an arg!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)

        msg.reply_text("The current warn limit is {}".format(limit))
    return ""

@kigcmd(command='strongwarn', filters=Filters.chat_type.groups)
@spamcheck
@u_admin(UserClass.ADMIN, AdminPerms.CAN_CHANGE_INFO)
def set_warn_strength(update: Update, context: CallbackContext):
    args = context.args
    chat: Optional[Chat] = update.effective_chat
    u: Optional[User] = update.effective_user
    msg: Optional[Message] = update.effective_message
    user = res_user(u, msg.message_id, chat)

    if args:
        if args[0].lower() in ("on", "yes"):
            sql.set_warn_strength(chat.id, False)
            msg.reply_text("Too many warns will now result in a Ban!")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has enabled strong warns. Users will be banned"
            )

        elif args[0].lower() in ("off", "no"):
            sql.set_warn_strength(chat.id, True)
            msg.reply_text(
                "Too many warns will now result in a kick! Users will be able to join again after."
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has disabled bans. I will just kick users."
            )

        else:
            msg.reply_text("I only understand on/yes/no/off!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)
        if soft_warn:
            msg.reply_text(
                "Warns are currently set to *kick* users when they exceed the limits.",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            msg.reply_text(
                "Warns are currently set to *Ban* users when they exceed the limits.",
                parse_mode=ParseMode.MARKDOWN,
            )
    return ""


def __stats__():
    return (
        f"• {sql.num_warns()} overall warns, across {sql.num_warn_chats()} chats.\n"
        f"• {sql.num_warn_filters()} warn filters, across {sql.num_warn_filter_chats()} chats."
    )


def __import_data__(chat_id, data):
    for user_id, count in data.get("warns", {}).items():
        for _ in range(int(count)):
            sql.warn_user(user_id, chat_id)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    num_warn_filters = sql.num_warn_chat_filters(chat_id)
    limit, soft_warn = sql.get_warn_setting(chat_id)
    return (
        f"This chat has `{num_warn_filters}` warn filters. "
        f"It takes `{limit}` warns before the user gets *{'kicked' if soft_warn else 'banned'}*."
    )


from tg_bot.modules.language import gs


def get_help(chat):
    return gs(chat, "warns_help")


__mod_name__ = "Warnings"
>>>>>>> 886c7d2ea... global fixes and enhancelments
