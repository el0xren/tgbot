from time import perf_counter
from functools import wraps
from cachetools import TTLCache
from threading import RLock
from typing import Optional

from telegram import User, Chat, ChatMember, Update, Bot, TelegramError

from tg_bot import dispatcher, CallbackContext, DEL_CMDS, OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, SUPPORT_CHAT

ADMIN_CACHE = TTLCache(maxsize=512, ttl=60 * 10, timer=perf_counter)
THREAD_LOCK = RLock()


def is_sudo_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return user_id in DEV_USERS or user_id in SUDO_USERS


def is_support_plus(chat: Chat,
                    user_id: int,
                    member: ChatMember = None) -> bool:
    return user_id in SUPPORT_USERS or user_id in SUDO_USERS


def is_whitelist_plus(chat: Chat,
                      user_id: int,
                      member: ChatMember = None) -> bool:
    return any(user_id in user
               for user in [WHITELIST_USERS, SUPPORT_USERS, SUDO_USERS])


def owner_plus(func):

    @wraps(func)
    def is_owner_plus_func(update: Update, context: CallbackContext, *args,
                           **kwargs):
        bot = context.bot
        user = update.effective_user

        if user.id == OWNER_ID:
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except TelegramError:
                pass
        else:
            update.effective_message.reply_text(
                "This is a restricted command. You do not have permissions to run this."
            )

    return is_owner_plus_func


def dev_plus(func):

    @wraps(func)
    def is_dev_plus_func(update: Update, context: CallbackContext, *args,
                         **kwargs):
        bot = context.bot
        user = update.effective_user  # type: Optional[User]

        if user.id in DEV_USERS:
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except TelegramError:
                pass
        else:
            update.effective_message.reply_text(
                "This is a developer restricted command. You do not have permissions to run this."
            )

    return is_dev_plus_func


def sudo_plus(func):

    @wraps(func)
    def is_sudo_plus_func(update: Update, context: CallbackContext, *args,
                          **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_sudo_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except TelegramError:
                pass
        else:
            update.effective_message.reply_text(
                "Who dis non-admin telling me what to do?")

    return is_sudo_plus_func


def support_plus(func):

    @wraps(func)
    def is_support_plus_func(update: Update, context: CallbackContext, *args,
                             **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_support_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except TelegramError:
                pass

    return is_support_plus_func


def whitelist_plus(func):

    @wraps(func)
    def is_whitelist_plus_func(update: Update, context: CallbackContext, *args,
                               **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_whitelist_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                f"You don't have access to use this.\nVisit @{SUPPORT_CHAT}")

    return is_whitelist_plus_func


def can_delete(chat: Chat, bot_id: int) -> bool:
    return chat.get_member(bot_id).can_delete_messages


def can_change_info(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).can_change_info


def is_user_ban_protected(chat: Chat,
                          user_id: int,
                          member: ChatMember = None) -> bool:
    if chat.type == 'private' \
            or user_id in DEV_USERS \
            or user_id in SUDO_USERS \
            or user_id in WHITELIST_USERS \
            or chat.all_members_are_administrators:
        return True

    if not member:
        member = chat.get_member(user_id)
    return member.status in ('administrator', 'creator')


def is_user_admin(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    if chat.type == 'private' \
            or user_id in DEV_USERS \
            or user_id in SUDO_USERS \
            or chat.all_members_are_administrators:
        return True

    if not member:
        with THREAD_LOCK:
            try:
                return user_id in ADMIN_CACHE[chat.id]
            except KeyError:
                chat_admins = dispatcher.bot.getChatAdministrators(chat.id)
                admin_list = [x.user.id for x in chat_admins]
                ADMIN_CACHE[chat.id] = admin_list

                return user_id in admin_list
    else:
        return member.status in ("administrator", "creator")


def is_bot_admin(chat: Chat,
                 bot_id: int,
                 bot_member: ChatMember = None) -> bool:
    if chat.type == 'private' \
            or chat.all_members_are_administrators:
        return True

    if not bot_member:
        bot_member = chat.get_member(bot_id)
    return bot_member.status in ('administrator', 'creator')


def is_user_in_chat(chat: Chat, user_id: int) -> bool:
    member = chat.get_member(user_id)
    return member.status not in ('left', 'kicked')


def bot_can_delete(func):

    @wraps(func)
    def delete_rights(update: Update, context: CallbackContext, *args,
                      **kwargs):
        bot = context.bot
        if can_delete(update.effective_chat, bot.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                "I can't delete messages here! "
                "Make sure I'm admin and can delete other user's messages.")

    return delete_rights


def can_pin(func):

    @wraps(func)
    def pin_rights(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        if update.effective_chat.get_member(bot.id).can_pin_messages:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                "I can't pin messages here! "
                "Make sure I'm admin and can pin messages.")

    return pin_rights


def can_promote(func):

    @wraps(func)
    def promote_rights(update: Update, context: CallbackContext, *args,
                       **kwargs):
        bot = context.bot
        if update.effective_chat.get_member(bot.id).can_promote_members:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                "I can't promote/demote people here! "
                "Make sure I'm admin and can appoint new admins.")

    return promote_rights


def can_restrict(func):

    @wraps(func)
    def promote_rights(update: Update, context: CallbackContext, *args,
                       **kwargs):
        bot = context.bot
        if update.effective_chat.get_member(bot.id).can_restrict_members:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                "I can't restrict people here! "
                "Make sure I'm admin and can appoint new admins.")

    return promote_rights


def bot_admin(func):

    @wraps(func)
    def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        if is_bot_admin(update.effective_chat, bot.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text("I'm not admin!")

    return is_admin


def user_admin(func):

    @wraps(func)
    def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        user = update.effective_user  # type: Optional[User]
        if user and is_user_admin(update.effective_chat, user.id):
            return func(update, context, *args, **kwargs)

        elif not user:
            pass

        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

        else:
            update.effective_message.reply_text(
                "Who dis non-admin telling me what to do?")

    return is_admin


def user_admin_no_reply(func):

    @wraps(func)
    def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        user = update.effective_user  # type: Optional[User]
        if user and is_user_admin(update.effective_chat, user.id):
            return func(update, context, *args, **kwargs)

        elif not user:
            pass

        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

    return is_admin


def user_not_admin(func):

    @wraps(func)
    def is_not_admin(update: Update, context: CallbackContext, *args,
                     **kwargs):
        bot = context.bot
        user = update.effective_user  # type: Optional[User]
        if user and not is_user_admin(update.effective_chat, user.id):
            return func(update, context, *args, **kwargs)

    return is_not_admin


def user_can_restrict_no_reply(func):

    @wraps(func)
    def user_can_restrict_noreply(update: Update, context: CallbackContext,
                                  *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat
        query = update.callback_query
        member = chat.get_member(user.id)

        if user:
            if member.can_restrict_members or member.status == "creator" or user.id in SUDO_USERS:
                return func(update, context, *args, **kwargs)
            elif member.status == 'administrator':
                query.answer(
                    "You lack the permission: `can_restrict_members` permission."
                )
            else:
                query.answer(
                    "You need to be admin with `can_restrict_users` permission to do this."
                )
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except:
                pass

    return user_can_restrict_noreply
