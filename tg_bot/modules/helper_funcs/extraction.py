from typing import List, Optional, Tuple

from telegram import Message, MessageEntity, ParseMode
from telegram.error import BadRequest

from tg_bot import LOGGER
from tg_bot.modules.users import get_user_id


def id_from_reply(message: Message) -> Tuple[Optional[int], Optional[str]]:
    prev_message = message.reply_to_message
    if not prev_message:
        return None, None

    user_id = None
    if prev_message.from_user:
        user_id = prev_message.from_user.id

    res = message.text.split(None, 1)
    text = res[1] if len(res) >= 2 else ""
    return user_id, text


def extract_user(message: Message, args: List[str]) -> Optional[int]:
    return extract_user_and_text(message, args)[0]


def extract_user_and_text(message: Message, args: List[str]) -> Tuple[Optional[int], Optional[str]]:
    prev_message = message.reply_to_message
    split_text = message.text.split(None, 1)

    if len(split_text) < 2 and not prev_message:
        return None, None

    text = ""
    user_id = None

    if prev_message:
        user_id, text = id_from_reply(message)
        if user_id:
            try:
                message.bot.get_chat(user_id)
                return user_id, text
            except BadRequest as excp:
                if excp.message in ("User_id_invalid", "Chat not found", "Chat_id is empty"):
                    message.reply_text(
                        "I don't seem to have interacted with this user before - please forward a message from "
                        "them to give me control! (like a voodoo doll, I need a piece of them to be able "
                        "to execute certain commands...)",
                        parse_mode=ParseMode.HTML)
                else:
                    message.reply_text(f"Error validating user: {excp.message}", parse_mode=ParseMode.HTML)
                return None, text
        else:
            message.reply_text(
                "Cannot extract a user from this forwarded message (possibly a channel or anonymous admin). "
                "Please use @username or user ID.",
                parse_mode=ParseMode.HTML)
            return None, text

    entities = list(message.parse_entities([MessageEntity.TEXT_MENTION]))
    text_to_parse = split_text[1] if len(split_text) >= 2 else ""
    if entities and len(text_to_parse) > 0:
        ent = entities[0]
        if ent.offset == len(message.text) - len(text_to_parse):
            user_id = ent.user.id
            text = message.text[ent.offset + ent.length:].strip()

    if not user_id and args and args[0]:
        first_arg = args[0].strip()
        text = " ".join(args[1:]).strip() if len(args) > 1 else ""
        if first_arg.startswith("@"):
            user_id = get_user_id(first_arg)
            if not user_id:
                message.reply_text(
                    "I don't have that user in my database. Please reply to their message, "
                    "forward one of their messages, or use their numeric user ID.",
                    parse_mode=ParseMode.HTML)
                return None, text
        elif first_arg.isdigit() and len(first_arg) >= 5:
            try:
                user_id = int(first_arg)
            except ValueError:
                message.reply_text("Invalid user ID format.", parse_mode=ParseMode.HTML)
                return None, text

    if user_id:
        try:
            message.bot.get_chat(user_id)
            return user_id, text
        except BadRequest as excp:
            if excp.message in ("User_id_invalid", "Chat not found", "Chat_id is empty"):
                message.reply_text(
                    "I don't seem to have interacted with this user before - please forward a message from "
                    "them to give me control! (like a voodoo doll, I need a piece of them to be able "
                    "to execute certain commands...)",
                    parse_mode=ParseMode.HTML)
            else:
                message.reply_text(f"Error validating user: {excp.message}", parse_mode=ParseMode.HTML)
            return None, text

    LOGGER.debug("No valid User ID extracted.")
    message.reply_text(
        "You don't seem to be referring to a user. Reply to a message, use @username, or provide a user ID.",
        parse_mode=ParseMode.HTML)
    return None, text


def extract_text(message: Message) -> str:
    """Extract text from message, caption, or sticker emoji."""
    return message.text or message.caption or (message.sticker.emoji if message.sticker else None)
