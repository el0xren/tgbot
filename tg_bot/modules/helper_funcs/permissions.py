from enum import Enum
import functools

from telegram import Update, ParseMode
from telegram.ext import CallbackContext

from tg_bot import dispatcher, DEV_USERS, SUDO_USERS


class AdminPerms(Enum):
    CAN_RESTRICT_MEMBERS = 'CanRestrictMembers'
    CAN_PROMOTE_MEMBERS = 'CanPromoteMembers'
    CAN_INVITE_USERS ='CanInviteUsers'
    CAN_DELETE_MESSAGES ='CanDeleteMessages'
    CAN_CHANGE_INFO ='CanChangeInfo'
    CAN_PIN_MESSAGES = 'CanPinMessages'
    IS_ANONYMOUS = 'IsAnonymous'


class ChatStatus(Enum):
    CREATOR = "creator"
    ADMIN   = "administrator"


def user_admin(ustat: UserClass, permission: AdminPerms):
    def wrapper(func):
        @functools.wraps(func)
        def awrapper(update: Update, context: CallbackContext, *args, **kwargs):
            nonlocal permission
            if update.effective_chat.type == 'private':
                return func(update, context, *args, **kwargs)
            message = update.effective_message
            user_id = message.from_user.id 
            chat_id = message.chat.id
            mem = context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if getattr(mem, permission.value) is True or mem.status == "creator" or user_id in DEV_USERS or user_id in SUDO_USERS:
                return func(update, context, *args, **kwargs)
            else:
                return message.reply_text(f"You are missing the following rights to use this command: {permission.name}")

        return awrapper
    return wrapper
