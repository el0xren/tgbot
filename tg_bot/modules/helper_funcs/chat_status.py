from time import perf_counter
from functools import wraps
from cachetools import TTLCache
from threading import RLock
from typing import Optional

from telegram import User, Chat, ChatMember, Update, TelegramError, ParseMode

from tg_bot import dispatcher, CallbackContext, DEL_CMDS, OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, SUPPORT_CHAT

ADMIN_CACHE = TTLCache(maxsize=512, ttl=60 * 10)
ADMIN_CACHE_LOCK = RLock()


def validate_user(update: Update, context: CallbackContext, user_id: int, sender_id: int, skip_privileged: bool = False) -> Optional[Chat]:
    bot = context.bot
    message = update.effective_message

    if not user_id or not isinstance(user_id, int):
        if message.reply_to_message:
            message.reply_text(
                "Cannot extract a user from this forwarded message (possibly a channel or anonymous admin). "
                "Please use @username or user ID.",
                parse_mode=ParseMode.HTML)
        else:
            message.reply_text(
                "You don't seem to be referring to a user. Reply to a message, use @username, or provide a user ID.",
                parse_mode=ParseMode.HTML)
        return None

    if user_id == sender_id:
        message.reply_text("You cannot act against yourself.", parse_mode=ParseMode.HTML)
        return None

    if user_id == bot.id:
        message.reply_text("I cannot act against myself.", parse_mode=ParseMode.HTML)
        return None

    if not skip_privileged:
        if int(user_id) == OWNER_ID:
            message.reply_text("I cannot act against bot owner.", parse_mode=ParseMode.HTML)
            return None
        if int(user_id) in DEV_USERS:
            message.reply_text("I cannot act against a developer.", parse_mode=ParseMode.HTML)
            return None
        if int(user_id) in SUDO_USERS:
            message.reply_text("I cannot act against a sudo user.", parse_mode=ParseMode.HTML)
            return None
        if int(user_id) in SUPPORT_USERS:
            message.reply_text("I cannot act against a support user.", parse_mode=ParseMode.HTML)
            return None

    try:
        user_chat = bot.get_chat(user_id)
        return user_chat
    except (BadRequest, TelegramError) as excp:
        message.reply_text(f"Error fetching user: {excp.message}", parse_mode=ParseMode.HTML)
        return None

def is_sudo_plus(_: Chat, user_id: int, member: ChatMember = None) -> bool:
    return user_id in SUDO_USERS or user_id in DEV_USERS


def is_support_plus(_: Chat, user_id: int, member: ChatMember = None) -> bool:
    return user_id in SUPPORT_USERS or user_id in DEV_USERS or user_id in SUDO_USERS


def is_whitelist_plus(_: Chat,
                      user_id: int,
                      member: ChatMember = None) -> bool:
    return any(
        user_id in user
        for user in [WHITELIST_USERS, SUPPORT_USERS, SUDO_USERS, DEV_USERS])


def owner_plus(func):

    @wraps(func)
    def is_owner_plus_func(update: Update, context: CallbackContext, *args,
                           **kwargs):
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
                "This is a restricted command. You do not have permissions to run this."
            )

    return is_sudo_plus_func


def support_plus(func):

    @wraps(func)
    def is_support_plus_func(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        chat = update.effective_chat

        if user and is_support_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.reply_text(
                "This is a restricted command. You do not have permissions to run this.",
                parse_mode=ParseMode.HTML
            )
            try:
                update.effective_message.delete()
            except TelegramError:
                pass
        else:
            update.effective_message.reply_text(
                "This is a restricted command. You do not have permissions to run this.",
                parse_mode=ParseMode.HTML
            )

    return is_support_plus_func


def whitelist_plus(func):

    @wraps(func)
    def is_whitelist_plus_func(update: Update, context: CallbackContext, *args,
                               **kwargs):
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


def user_can_delete(chat: Chat, user_id: int) -> bool:
    mem = chat.get_member(user_id)
    return bool(mem.can_delete_messages or mem.status == "creator"
                or user_id in DEV_USERS or SUDO_USERS)


def can_change_info(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).can_change_info


def user_can_change_info(chat: Chat, user_id: int) -> bool:
    mem = chat.get_member(user_id)
    return bool(mem.can_change_info or mem.status == "creator"
                or user_id in DEV_USERS or SUDO_USERS)


def is_user_ban_protected(update: Update,
                          user_id: int,
                          member: ChatMember = None) -> bool:
    chat = update.effective_chat
    msg = update.effective_message
    if chat.type == 'private' \
            or user_id in DEV_USERS \
            or user_id in SUDO_USERS \
            or user_id in WHITELIST_USERS \
            or chat.all_members_are_administrators \
            or (msg.reply_to_message and msg.reply_to_message.sender_chat is not None
            and msg.reply_to_message.sender_chat.type != "channel"):
        return True

    if not member:
        member = chat.get_member(user_id)
    return member.status in ('administrator', 'creator')


def is_user_admin(chat_or_update: Update | Chat, user_id: int, member: ChatMember = None) -> bool:
    if isinstance(chat_or_update, Update):
        chat = chat_or_update.effective_chat
        msg = chat_or_update.effective_message
    else:
        chat = chat_or_update
        msg = None

    if chat.type == 'private' \
            or user_id in DEV_USERS \
            or user_id in SUDO_USERS \
            or chat.all_members_are_administrators \
            or (msg and msg.reply_to_message and msg.reply_to_message.sender_chat is not None and
                msg.reply_to_message.sender_chat.type != "channel"):
        return True

    if not member:
        with ADMIN_CACHE_LOCK:
            if user_id in ADMIN_CACHE.get(chat.id, []):
                return True
            try:
                chat_admins = dispatcher.bot.getChatAdministrators(chat.id)
                admin_list = [x.user.id for x in chat_admins]
                ADMIN_CACHE[chat.id] = admin_list
                return user_id in admin_list
            except TelegramError as excp:
                message.reply_text(f"Error checking admin status for user {user_id} in chat {chat.id}: {excp.message}", parse_mode=ParseMode.HTML)
                return False


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
        if user and is_user_admin(update, user.id):
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
        if user and is_user_admin(update, user.id):
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
        message = update.effective_message
        user = update.effective_user

        if message.is_automatic_forward:
            return
        if message.sender_chat and message.sender_chat.type != "channel":
            return
        elif user and not is_user_admin(update, user.id):
            return func(update, context, *args, **kwargs)

        elif not user:
            pass

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
                    "You are missing the following rights to use this command: CanRestrictUsers"
                )
            else:
                query.answer(
                    "You are missing the following rights to use this command: CanRestrictUsers"
                )
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except:
                pass

    return user_can_restrict_noreply
