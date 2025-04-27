from enum import Enum
import functools

from telegram import Update, ParseMode, User
from telegram.ext import CallbackContext

from tg_bot import dispatcher, DEV_USERS, SUDO_USERS


class AdminPerms(Enum):
    CAN_CHANGE_INFO = 'can_change_info'
    CAN_POST_MESSAGES = 'can_post_messages'
    CAN_EDIT_MESSAGES = 'can_edit_messages'
    CAN_DELETE_MESSAGES = 'can_delete_messages'
    CAN_INVITE_USERS = 'can_invite_users'
    CAN_RESTRICT_MEMBERS = 'can_restrict_members'
    CAN_PIN_MESSAGES = 'can_pin_messages'
    CAN_PROMOTE_MEMBERS = 'can_promote_members'
    IS_ANONYMOUS = 'is_anonymous'
    CAN_MANAGE_VOICE_CHATS = 'can_manage_voice_chats'
    CAN_MANAGE_CHAT = 'can_manage_chat'
    CAN_MANAGE_TOPICS = 'can_manage_topics'



class ChatStatus(Enum):
    CREATOR = "creator"
    ADMIN = "administrator"


def user_admin(permission: AdminPerms):
    def wrapper(func):
        @functools.wraps(func)
        def awrapper(update: Update, context: CallbackContext, *args, **kwargs):
            if update.effective_chat.type == 'private':
                return func(update, context, *args, **kwargs)

            message = update.effective_message
            user_id = message.from_user.id
            chat_id = message.chat.id
            mem = context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)

            if (
                getattr(mem, permission.value, False)
                or mem.status == "creator"
                or user_id in DEV_USERS
                or user_id in SUDO_USERS
            ):
                return func(update, context, *args, **kwargs)
            else:
                return message.reply_text(
                    f"You are missing the following rights to use this command: {permission.name.replace('_', ' ').title()}"
                )
        return awrapper
    return wrapper
