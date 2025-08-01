import html
import re
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import MessageHandler, Filters, CommandHandler, run_async, ChatJoinRequestHandler, CallbackQueryHandler
from telegram.utils.helpers import mention_markdown, mention_html, escape_markdown
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup

import tg_bot.modules.sql.welcome_sql as sql
from tg_bot import dispatcher, CallbackContext, OWNER_ID, DEV_USERS, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_admin, user_can_restrict_no_reply, bot_admin
from tg_bot.modules.helper_funcs.misc import build_keyboard, revert_buttons
from tg_bot.modules.helper_funcs.msg_types import get_welcome_type
from tg_bot.modules.helper_funcs.string_handling import markdown_parser, \
    escape_invalid_curly_brackets
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql.global_bans_sql import is_user_gbanned
from tg_bot.modules.helper_funcs.misc import send_to_list

VALID_WELCOME_FORMATTERS = [
    'first', 'last', 'fullname', 'username', 'id', 'count', 'chatname',
    'mention'
]

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video
}


def send(update, message, keyboard, backup_message):
    chat = update.effective_chat
    cleanserv = sql.clean_service(chat.id)
    reply = update.message.message_id if update.message else None
    thread_id = update.message.message_thread_id if update.message else None

    if cleanserv:
        try:
            dispatcher.bot.delete_message(chat.id, update.message.message_id)
        except BadRequest:
            pass
        reply = False

    msg = None

    try:
        msg = update.effective_message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
            reply_to_message_id=reply,
            message_thread_id=thread_id,
            allow_sending_without_reply=True
        )
    except BadRequest as excp:
        if excp.message == "Not enough rights to send text messages to the chat":
            LOGGER.warning(f"Cannot send message to chat {chat.id} (topic {thread_id}): Bot lacks permission to send messages.")
            try:
                admin_chat_id = chat.id
                dispatcher.bot.send_message(
                    admin_chat_id,
                    f"Failed to send welcome message in chat {chat.title} (ID: {chat.id}, Topic ID: {thread_id or 'General'}) because the bot lacks permission to send messages.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except BadRequest as admin_excp:
                LOGGER.error(f"Failed to notify admins: {admin_excp.message}")
            return None
        elif excp.message == "Topic_closed":
            LOGGER.warning(f"Cannot send message to chat {chat.id}, topic {thread_id}: Topic is closed.")
            return None
        elif excp.message == "Reply message not found":
            msg = update.effective_message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
                quote=False,
                message_thread_id=thread_id
            )
        elif excp.message == "Button_url_invalid":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message +
                    "\nNote: the current message has an invalid url in one of its buttons. Please update."
                ),
                parse_mode=ParseMode.MARKDOWN
            )
        elif excp.message == "Unsupported url protocol":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message +
                    "\nNote: the current message has buttons which use url protocols that are unsupported by telegram. Please update."
                ),
                parse_mode=ParseMode.MARKDOWN
            )
        elif excp.message == "Wrong url host":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message +
                    "\nNote: the current message has some bad urls. Please update."
                ),
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(message)
            LOGGER.warning(keyboard)
            LOGGER.exception("Could not parse! got invalid url host errors")
        else:
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message +
                    "\nNote: An error occurred when sending the custom message. Please update."
                ),
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.exception(f"Unexpected error: {excp.message}")

    except IndexError:
        msg = update.effective_message.reply_text(
            markdown_parser(
                backup_message +
                "\nNote: the current message was invalid due to markdown issues. Could be due to the user's name."
            ),
            parse_mode=ParseMode.MARKDOWN
        )
    except KeyError:
        msg = update.effective_message.reply_text(
            markdown_parser(
                backup_message +
                "\nNote: the current message is invalid due to an issue with some misplaced curly brackets. Please update"
            ),
            parse_mode=ParseMode.MARKDOWN
        )

    if msg is None:
        LOGGER.error("Fallback triggered in send(); original message couldn't be sent.")
        return None

    return msg


def new_member(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    reply = update.message.message_id
    should_welc, cust_welcome, welc_type = sql.get_welc_pref(chat.id)
    if should_welc:
        sent = None
        reply = update.message.message_id
        cleanserv = sql.clean_service(chat.id)
        # Clean service welcome
        if cleanserv:
            try:
                dispatcher.bot.delete_message(chat.id,
                                              update.message.message_id)
            except BadRequest:
                pass
            reply = False
        new_members = update.effective_message.new_chat_members
        for new_mem in new_members:

            if is_user_gbanned(new_mem.id):
                return

            # Give the owner a special welcome
            if new_mem.id == OWNER_ID:
                update.effective_message.reply_text(
                    "Master is in the houseeee, let's get this party started!")
                continue

            # Give the devs a special welcome
            elif new_mem.id in DEV_USERS:
                update.effective_message.reply_text(
                    "Naisu! One of developers just jumped in >.<")
                continue

            # Welcome yourself
            elif new_mem.id == bot.id:
                update.effective_message.reply_text(
                    "Hewwo! Thanks for adding me >.<",
                    reply_to_message_id=reply)
                continue

            else:
                # If welcome message is media, send with appropriate function
                if welc_type != sql.Types.TEXT and welc_type != sql.Types.BUTTON_TEXT:
                    ENUM_FUNC_MAP[welc_type](chat.id, cust_welcome)
                    return
                # else, move on
                first_name = new_mem.first_name or "PersonWithNoName"  # edge case of empty name - occurs for some bugs.

                if cust_welcome:
                    if new_mem.last_name:
                        fullname = "{} {}".format(first_name,
                                                  new_mem.last_name)
                    else:
                        fullname = first_name
                    count = chat.get_member_count()
                    mention = mention_markdown(new_mem.id, first_name)
                    if new_mem.username:
                        username = "@" + escape_markdown(new_mem.username)
                    else:
                        username = mention

                    valid_format = escape_invalid_curly_brackets(
                        cust_welcome, VALID_WELCOME_FORMATTERS)
                    res = valid_format.format(
                        first=escape_markdown(first_name),
                        last=escape_markdown(new_mem.last_name or first_name),
                        fullname=escape_markdown(fullname),
                        username=username,
                        mention=mention,
                        count=count,
                        chatname=escape_markdown(chat.title),
                        id=new_mem.id)
                    buttons = sql.get_welc_buttons(chat.id)
                    keyb = build_keyboard(buttons)
                else:
                    res = sql.DEFAULT_WELCOME.format(first=first_name)
                    keyb = []

                keyboard = InlineKeyboardMarkup(keyb)

                sent = send(update, res, keyboard,
                            sql.DEFAULT_WELCOME.format(
                                first=first_name))  # type: Optional[Message]

        prev_welc = sql.get_clean_pref(chat.id)
        if prev_welc:
            try:
                bot.delete_message(chat.id, prev_welc)
            except BadRequest as excp:
                pass

            if sent:
                sql.set_clean_welcome(chat.id, sent.message_id)


def left_member(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    should_goodbye, cust_goodbye, goodbye_type = sql.get_gdbye_pref(chat.id)
    if should_goodbye:
        reply = update.message.message_id
        cleanserv = sql.clean_service(chat.id)
        # Clean service welcome
        if cleanserv:
            try:
                dispatcher.bot.delete_message(chat.id,
                                              update.message.message_id)
            except BadRequest:
                pass
            reply = False
        left_mem = update.effective_message.left_chat_member
        if left_mem:

            if is_user_gbanned(left_mem.id):
                return

            # Ignore bot being kicked
            if left_mem.id == bot.id:
                return

            # Give the owner a special goodbye
            if left_mem.id == OWNER_ID:
                update.effective_message.reply_text("RIP Master")
                return

            # Give the devs a special goodbye
            elif left_mem.id in DEV_USERS:
                update.effective_message.reply_text("See you later developer!")
                return

            # if media goodbye, use appropriate function for it
            if goodbye_type != sql.Types.TEXT and goodbye_type != sql.Types.BUTTON_TEXT:
                ENUM_FUNC_MAP[goodbye_type](chat.id, cust_goodbye)
                return

            first_name = left_mem.first_name or "PersonWithNoName"  # edge case of empty name - occurs for some bugs.
            if cust_goodbye:
                if left_mem.last_name:
                    fullname = "{} {}".format(first_name, left_mem.last_name)
                else:
                    fullname = first_name
                count = chat.get_member_count()
                mention = mention_markdown(left_mem.id, first_name)
                if left_mem.username:
                    username = "@" + escape_markdown(left_mem.username)
                else:
                    username = mention

                valid_format = escape_invalid_curly_brackets(
                    cust_goodbye, VALID_WELCOME_FORMATTERS)
                res = valid_format.format(
                    first=escape_markdown(first_name),
                    last=escape_markdown(left_mem.last_name or first_name),
                    fullname=escape_markdown(fullname),
                    username=username,
                    mention=mention,
                    count=count,
                    chatname=escape_markdown(chat.title),
                    id=left_mem.id)
                buttons = sql.get_gdbye_buttons(chat.id)
                keyb = build_keyboard(buttons)

            else:
                res = sql.DEFAULT_GOODBYE
                keyb = []

            keyboard = InlineKeyboardMarkup(keyb)

            send(update, res, keyboard, sql.DEFAULT_GOODBYE)


@user_admin
def welcome(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    # if no args, show current replies.
    if len(args) == 0 or args[0].lower() == "noformat":
        noformat = args and args[0].lower() == "noformat"
        pref, welcome_m, welcome_type = sql.get_welc_pref(chat.id)
        update.effective_message.reply_text(
            "This chat has it's welcome setting set to: `{}`.\n*The welcome message "
            "(not filling the {{}}) is:*".format(pref),
            parse_mode=ParseMode.MARKDOWN)

        if welcome_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                update.effective_message.reply_text(welcome_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, welcome_m, keyboard, sql.DEFAULT_WELCOME)

        else:
            if noformat:
                ENUM_FUNC_MAP[welcome_type](chat.id, welcome_m)

            else:
                ENUM_FUNC_MAP[welcome_type](chat.id,
                                            welcome_m,
                                            parse_mode=ParseMode.MARKDOWN)

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_welc_preference(str(chat.id), True)
            update.effective_message.reply_text("I'll be polite!")

        elif args[0].lower() in ("off", "no"):
            sql.set_welc_preference(str(chat.id), False)
            update.effective_message.reply_text(
                "I'm sulking, not saying hello anymore.")

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text(
                "I understand 'on/yes' or 'off/no' only!")


@user_admin
def goodbye(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]

    if len(args) == 0 or args[0] == "noformat":
        noformat = args and args[0] == "noformat"
        pref, goodbye_m, goodbye_type = sql.get_gdbye_pref(chat.id)
        update.effective_message.reply_text(
            "This chat has it's goodbye setting set to: `{}`.\n*The goodbye  message "
            "(not filling the {{}}) is:*".format(pref),
            parse_mode=ParseMode.MARKDOWN)

        if goodbye_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_gdbye_buttons(chat.id)
            if noformat:
                goodbye_m += revert_buttons(buttons)
                update.effective_message.reply_text(goodbye_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, goodbye_m, keyboard, sql.DEFAULT_GOODBYE)

        else:
            if noformat:
                ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m)

            else:
                ENUM_FUNC_MAP[goodbye_type](chat.id,
                                            goodbye_m,
                                            parse_mode=ParseMode.MARKDOWN)

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_gdbye_preference(str(chat.id), True)
            update.effective_message.reply_text(
                "I'll be sorry when people leave!")

        elif args[0].lower() in ("off", "no"):
            sql.set_gdbye_preference(str(chat.id), False)
            update.effective_message.reply_text(
                "They leave, they're dead to me.")

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text(
                "I understand 'on/yes' or 'off/no' only!")


@user_admin
@loggable
def set_welcome(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("You didn't specify what to reply with!")
        return ""

    sql.set_custom_welcome(chat.id, content or text, data_type, buttons)
    msg.reply_text("Successfully set custom welcome message!")

    return "<b>{}:</b>" \
           "\n#SET_WELCOME" \
           "\n<b>Admin:</b> {}" \
           "\nSet the welcome message.".format(html.escape(chat.title),
                                               mention_html(user.id, user.first_name))


@user_admin
@loggable
def reset_welcome(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    sql.set_custom_welcome(chat.id, sql.DEFAULT_WELCOME, sql.Types.TEXT)
    update.effective_message.reply_text(
        "Successfully reset welcome message to default!")
    return "<b>{}:</b>" \
           "\n#RESET_WELCOME" \
           "\n<b>Admin:</b> {}" \
           "\nReset the welcome message to default.".format(html.escape(chat.title),
                                                            mention_html(user.id, user.first_name))


@user_admin
@loggable
def set_goodbye(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("You didn't specify what to reply with!")
        return ""

    sql.set_custom_gdbye(chat.id, content or text, data_type, buttons)
    msg.reply_text("Successfully set custom goodbye message!")
    return "<b>{}:</b>" \
           "\n#SET_GOODBYE" \
           "\n<b>Admin:</b> {}" \
           "\nSet the goodbye message.".format(html.escape(chat.title),
                                               mention_html(user.id, user.first_name))


@user_admin
@loggable
def reset_goodbye(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    sql.set_custom_gdbye(chat.id, sql.DEFAULT_GOODBYE, sql.Types.TEXT)
    update.effective_message.reply_text(
        "Successfully reset goodbye message to default!")
    return "<b>{}:</b>" \
           "\n#RESET_GOODBYE" \
           "\n<b>Admin:</b> {}" \
           "\nReset the goodbye message.".format(html.escape(chat.title),
                                                 mention_html(user.id, user.first_name))


@user_admin
@loggable
def clean_welcome(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if not args:
        clean_pref = sql.get_clean_pref(chat.id)
        if clean_pref:
            update.effective_message.reply_text(
                "I should be deleting welcome messages up to two days old.")
        else:
            update.effective_message.reply_text(
                "I'm currently not deleting old welcome messages!")
        return ""

    if args[0].lower() in ("on", "yes"):
        sql.set_clean_welcome(str(chat.id), True)
        update.effective_message.reply_text(
            "I'll try to delete old welcome messages!")
        return "<b>{}:</b>" \
               "\n#CLEAN_WELCOME" \
               "\n<b>Admin:</b> {}" \
               "\nHas toggled clean welcomes to <code>ON</code>.".format(html.escape(chat.title),
                                                                         mention_html(user.id, user.first_name))
    elif args[0].lower() in ("off", "no"):
        sql.set_clean_welcome(str(chat.id), False)
        update.effective_message.reply_text(
            "I won't delete old welcome messages.")
        return "<b>{}:</b>" \
               "\n#CLEAN_WELCOME" \
               "\n<b>Admin:</b> {}" \
               "\nHas toggled clean welcomes to <code>OFF</code>.".format(html.escape(chat.title),
                                                                          mention_html(user.id, user.first_name))
    else:
        # idek what you're writing, say yes or no
        update.effective_message.reply_text(
            "I understand 'on/yes' or 'off/no' only!")
        return ""


@user_admin
def cleanservice(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            if var in ("no", "off"):
                sql.set_clean_service(chat.id, False)
                update.effective_message.reply_text(
                    "Welcome clean service is off")
            elif var in ("yes", "on"):
                sql.set_clean_service(chat.id, True)
                update.effective_message.reply_text(
                    "Welcome clean service is on")
            else:
                update.effective_message.reply_text("Invalid option",
                                                    parse_mode=ParseMode.HTML)
        else:
            update.effective_message.reply_text(
                "I understand 'on/yes' or 'off/no' only!")
    else:
        curr = sql.clean_service(chat.id)
        if curr:
            update.effective_message.reply_text(
                "Welcome clean service is: <code>on</code>",
                parse_mode=ParseMode.HTML)
        else:
            update.effective_message.reply_text(
                "Welcome clean service is: <code>off</code>",
                parse_mode=ParseMode.HTML)


def chat_join_req(update: Update, context: CallbackContext):
    bot = context.bot
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve",
                             callback_data="cb_approve={}".format(user.id)),
        InlineKeyboardButton("❌ Decline",
                             callback_data="cb_decline={}".format(user.id)),
    ]])
    bot.send_message(chat.id,
                     "{} wants to join {}".format(
                         mention_html(user.id, user.first_name), chat.title
                         or "this chat"),
                     reply_markup=keyboard,
                     parse_mode=ParseMode.HTML)


@user_can_restrict_no_reply
@bot_admin
@loggable
def approve_join_req(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    match = re.match(r"cb_approve=(.+)", query.data)

    user_id = match.group(1)
    try:
        bot.approve_chat_join_request(chat.id, user_id)
        update.effective_message.edit_text(
            f"Join request approved by {mention_html(user.id, user.first_name)}.",
            parse_mode=ParseMode.HTML)

        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#JOIN_REQUEST\n"
            f"Approved\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_id, html.escape(user.first_name))}\n"
        )

        return log

    except Exception as e:
        update.effective_message.edit_text(str(e))
        pass


@user_can_restrict_no_reply
@bot_admin
@loggable
def decline_join_req(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    match = re.match(r"cb_decline=(.+)", query.data)

    user_id = match.group(1)
    try:
        bot.decline_chat_join_request(chat.id, user_id)
        update.effective_message.edit_text(
            f"Join request declined by {mention_html(user.id, user.first_name)}.",
            parse_mode=ParseMode.HTML)

        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#JOIN_REQUEST\n"
            f"Declined!\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_id, html.escape(user.first_name))}\n"
        )

        return log

    except Exception as e:
        update.effective_message.edit_text(str(e))
        pass


WELC_HELP_TXT = "Your group's welcome/goodbye messages can be personalised in multiple ways. If you want the messages" \
                " to be individually generated, like the default welcome message is, you can use *these* variables:\n" \
                " - `{{first}}`: this represents the user's *first* name\n" \
                " - `{{last}}`: this represents the user's *last* name. Defaults to *first name* if user has no " \
                "last name.\n" \
                " - `{{fullname}}`: this represents the user's *full* name. Defaults to *first name* if user has no " \
                "last name.\n" \
                " - `{{username}}`: this represents the user's *username*. Defaults to a *mention* of the user's " \
                "first name if has no username.\n" \
                " - `{{mention}}`: this simply *mentions* a user - tagging them with their first name.\n" \
                " - `{{id}}`: this represents the user's *id*\n" \
                " - `{{count}}`: this represents the user's *member number*.\n" \
                " - `{{chatname}}`: this represents the *current chat name*.\n" \
                "\nEach variable MUST be surrounded by `{{}}` to be replaced.\n" \
                "Welcome messages also support markdown, so you can make any elements bold/italic/code/links. " \
                "Buttons are also supported, so you can make your welcomes look awesome with some nice intro " \
                "buttons.\n" \
                "To create a button linking to your rules, use this: `[Rules](buttonurl://t.me/{}?start=group_id)`. " \
                "Simply replace `group_id` with your group's id, which can be obtained via /id, and you're good to " \
                "go. Note that group ids are usually preceded by a `-` sign; this is required, so please don't " \
                "remove it.\n" \
                "If you're feeling fun, you can even set images/gifs/videos/voice messages as the welcome message by " \
                "replying to the desired media, and calling /setwelcome.".format(dispatcher.bot.username)


@user_admin
def welcome_help(update: Update, context: CallbackContext):
    bot = context.bot
    update.effective_message.reply_text(WELC_HELP_TXT,
                                        parse_mode=ParseMode.MARKDOWN)


# TODO: get welcome data from group butler snap
# def __import_data__(chat_id, data):
#     welcome = data.get('info', {}).get('rules')
#     welcome = welcome.replace('$username', '{username}')
#     welcome = welcome.replace('$name', '{fullname}')
#     welcome = welcome.replace('$id', '{id}')
#     welcome = welcome.replace('$title', '{chatname}')
#     welcome = welcome.replace('$surname', '{lastname}')
#     welcome = welcome.replace('$rules', '{rules}')
#     sql.set_custom_welcome(chat_id, welcome, sql.Types.TEXT)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    welcome_pref, _, _ = sql.get_welc_pref(chat_id)
    goodbye_pref, _, _ = sql.get_gdbye_pref(chat_id)
    return "This chat has it's welcome preference set to `{}`.\n" \
           "It's goodbye preference is `{}`.".format(welcome_pref, goodbye_pref)


__help__ = """
{}

*Admin only:*
 - /welcome <on/off>: enable/disable welcome messages.
 - /welcome: shows current welcome settings.
 - /welcome noformat: shows current welcome settings, without the formatting - useful to recycle your welcome messages!
 - /goodbye -> same usage and args as /welcome.
 - /setwelcome <sometext>: set a custom welcome message. If used replying to media, uses that media.
 - /setgoodbye <sometext>: set a custom goodbye message. If used replying to media, uses that media.
 - /resetwelcome: reset to the default welcome message.
 - /resetgoodbye: reset to the default goodbye message.
 - /cleanwelcome <on/off>: On new member, try to delete the previous welcome message to avoid spamming the chat.
 - /cleanservice <on/off: deletes telegrams welcome/left service messages. 
 - /welcomehelp: view more formatting information for custom welcome/goodbye messages.
""".format(WELC_HELP_TXT)

__mod_name__ = "Welcomes/Goodbyes"

NEW_MEM_HANDLER = MessageHandler(Filters.status_update.new_chat_members,
                                 new_member,
                                 run_async=True)
LEFT_MEM_HANDLER = MessageHandler(Filters.status_update.left_chat_member,
                                  left_member,
                                  run_async=True)
WELC_PREF_HANDLER = CommandHandler("welcome",
                                   welcome,
                                   run_async=True,
                                   filters=Filters.chat_type.groups)
GOODBYE_PREF_HANDLER = CommandHandler("goodbye",
                                      goodbye,
                                      run_async=True,
                                      filters=Filters.chat_type.groups)
SET_WELCOME = CommandHandler("setwelcome",
                             set_welcome,
                             filters=Filters.chat_type.groups,
                             run_async=True)
SET_GOODBYE = CommandHandler("setgoodbye",
                             set_goodbye,
                             filters=Filters.chat_type.groups,
                             run_async=True)
RESET_WELCOME = CommandHandler("resetwelcome",
                               reset_welcome,
                               filters=Filters.chat_type.groups,
                               run_async=True)
RESET_GOODBYE = CommandHandler("resetgoodbye",
                               reset_goodbye,
                               filters=Filters.chat_type.groups,
                               run_async=True)
CLEAN_WELCOME = CommandHandler("cleanwelcome",
                               clean_welcome,
                               run_async=True,
                               filters=Filters.chat_type.groups)
CLEAN_SERVICE_HANDLER = CommandHandler("cleanservice",
                                       cleanservice,
                                       filters=Filters.chat_type.groups,
                                       run_async=True)
WELCOME_HELP = CommandHandler("welcomehelp", welcome_help, run_async=True)

dispatcher.add_handler(NEW_MEM_HANDLER)
dispatcher.add_handler(LEFT_MEM_HANDLER)
dispatcher.add_handler(WELC_PREF_HANDLER)
dispatcher.add_handler(GOODBYE_PREF_HANDLER)
dispatcher.add_handler(SET_WELCOME)
dispatcher.add_handler(SET_GOODBYE)
dispatcher.add_handler(RESET_WELCOME)
dispatcher.add_handler(RESET_GOODBYE)
dispatcher.add_handler(CLEAN_WELCOME)
dispatcher.add_handler(CLEAN_SERVICE_HANDLER)
dispatcher.add_handler(
    ChatJoinRequestHandler(callback=chat_join_req, run_async=True))
dispatcher.add_handler(
    CallbackQueryHandler(approve_join_req,
                         pattern=r"cb_approve=",
                         run_async=True))
dispatcher.add_handler(
    CallbackQueryHandler(decline_join_req,
                         pattern=r"cb_decline=",
                         run_async=True))
dispatcher.add_handler(WELCOME_HELP)
