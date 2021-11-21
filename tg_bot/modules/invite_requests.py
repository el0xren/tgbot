import re
import html

from telegram import ParseMode
from telegram.update import Update
from telegram.ext import ChatJoinRequestHandler, CallbackQueryHandler
from telegram.ext.callbackcontext import CallbackContext
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.utils.helpers import mention_html

from ..import dispatcher
from .helper_funcs.chat_status import user_can_resrtict_no_reply, bot_admin

from .log_channel import loggable

def chat_join_req(upd: Update, ctx: CallbackContext):
    bot = ctx.bot
    user = upd.chat_join_request.from_user
    chat = upd.chat_join_request.chat
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve", callback_data="cb_approve={}".format(user.id)
                ),
                InlineKeyboardButton(
                    "❌ Decline", callback_data="cb_decline={}".format(user.id)
                ),
            ]
        ]
    )
    bot.send_message(
        chat.id,
        "{} wants to join {}".format(
            mention_html(user.id, user.first_name), chat.title or "this chat"
        ),
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


@user_can_resrtict_no_reply
@bot_admin
@loggable
def approve_joinreq(upd: Update, ctx: CallbackContext) -> str:
    bot = ctx.bot
    query = upd.callback_query
    user = upd.effective_user
    chat = upd.effective_chat
    match = re.match(r"cb_approve=(.+)", query.data)

    user_id = match.group(1)
    chat = upd.effective_chat.id
    try:
        bot.approve_chat_join_request(chat, user_id)
        upd.effective_message.edit_text(
            f"Join Request approved by {mention_html(user.id, user.first_name)}.",
            parse_mode="HTML",
        )
        logmsg = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#JOIN_REQUEST\n"
                f"Approved\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
                f"<b>User:</b> {mention_html(user_id, html.escape(user.first_name))}\n"
        )
        return logmsg
    except:
        pass

@user_can_resrtict_no_reply
@bot_admin
@loggable
def decline_joinreq(upd: Update, ctx: CallbackContext) -> str:
    bot = ctx.bot
    query = upd.callback_query
    user = upd.effective_user
    chat = upd.effective_chat
    match = re.match(r"cb_decline=(.+)", query.data)

    user_id = match.group(1)
    chat = upd.effective_chat.id
    try:
        bot.decline_chat_join_request(chat, user_id)
        upd.effective_message.edit_text(
            f"Join Request declined by {mention_html(user.id, user.first_name)}.",
            parse_mode="HTML",
        )
        logmsg = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#JOIN_REQUEST\n"
                f"Declined\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
                f"<b>User:</b> {mention_html(user_id, html.escape(user.first_name))}\n"
        )
        return logmsg
    except:
        pass


dispatcher.add_handler(ChatJoinRequestHandler(callback=chat_join_req, run_async=True))
dispatcher.add_handler(CallbackQueryHandler(approve_joinreq, pattern=r"cb_approve=", run_async=True))
dispatcher.add_handler(CallbackQueryHandler(decline_joinreq, pattern=r"cb_decline=", run_async=True))
