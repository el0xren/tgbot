import hashlib
import os
import math
import requests
from PIL import Image
from typing import Optional, List
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, Update, InputFile
from telegram.error import BadRequest, TelegramError
from telegram.ext import CommandHandler, CallbackContext
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler


def stickerid(update: Update, context: CallbackContext):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        update.effective_message.reply_text(
            "Sticker ID:\n```" + escape_markdown(msg.reply_to_message.sticker.file_id) + "```",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        update.effective_message.reply_text("Please reply to a sticker to get its ID.")


def getsticker(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        file_id = msg.reply_to_message.sticker.file_id
        sticker = msg.reply_to_message.sticker
        kang_file = bot.get_file(file_id)
        if kang_file.file_path.endswith('.webm'):
            msg.reply_text("Video stickers (WebM) are not supported in this bot version.")
            return
        file_ext = '.tgs' if sticker.is_animated else '.png'
        file_name = f'sticker{file_ext}'
        
        kang_file.download(file_name)
        
        with open(file_name, 'rb') as f:
            if file_ext == '.tgs':
                bot.send_document(chat_id, document=f)
            else:
                bot.send_document(chat_id, document=f)
        
        os.remove(file_name)
    else:
        update.effective_message.reply_text("Please reply to a sticker to upload its raw file.")


def kang(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    msg = update.effective_message
    user = update.effective_user

    sticker_emoji = args[0] if args else "🤔"
    hash = hashlib.sha1(bytearray(user.id)).hexdigest()
    packname = f"a{hash[:20]}_by_{bot.username}"
    file_name = None

    try:
        if msg.reply_to_message and msg.reply_to_message.sticker:
            sticker = msg.reply_to_message.sticker
            file_id = sticker.file_id
            kang_file = bot.get_file(file_id)
            if kang_file.file_path.endswith('.webm'):
                msg.reply_text("Video stickers (WebM) are not supported in this bot version.")
                return
            file_ext = '.tgs' if sticker.is_animated else '.png'
            file_name = f'kangsticker{file_ext}'
            
            kang_file.download(file_name)

            if file_ext == '.png':
                im = Image.open(file_name)
                maxsize = (512, 512)
                if im.size[0] > maxsize[0] or im.size[1] > maxsize[1]:
                    im.thumbnail(maxsize, Image.LANCZOS)
                elif im.size[0] < maxsize[0] and im.size[1] < maxsize[1]:
                    scale = min(maxsize[0] / im.size[0], maxsize[1] / im.size[1])
                    new_size = (int(im.size[0] * scale), int(im.size[1] * scale))
                    im = im.resize(new_size, Image.LANCZOS)
                im.save(file_name, "PNG")
                sticker_params = {"png_sticker": open(file_name, 'rb')}
            
            else:
                sticker_params = {"tgs_sticker": open(file_name, 'rb')}

            sticker_emoji = sticker.emoji if sticker.emoji and not args else sticker_emoji

            try:
                bot.add_sticker_to_set(user_id=user.id, name=packname, emojis=sticker_emoji, **sticker_params)
                msg.reply_text(
                    f"Sticker successfully added to [pack](t.me/addstickers/{packname})\nEmoji: {sticker_emoji}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except TelegramError as e:
                if e.message == "Stickerset_invalid":
                    makepack_internal(update, context, msg, user, sticker_emoji, packname, **sticker_params)
                elif e.message in ("Sticker_png_dimensions", "Sticker_png_invalid"):
                    msg.reply_text("Invalid static sticker dimensions or format.")
                elif e.message == "Sticker_tgs_invalid":
                    msg.reply_text("Invalid animated sticker format.")
                elif e.message == "Invalid sticker emojis":
                    msg.reply_text("Invalid emoji(s).")
                elif e.message == "Stickers_too_much":
                    msg.reply_text("Max pack size reached.")
                else:
                    msg.reply_text(f"Error: {e.message}")
                print(e)

        elif args and len(args) >= 1:
            try:
                url = args[1] if len(args) > 1 else args[0]
                sticker_emoji = args[2] if len(args) > 2 else "🤔"
                file_name = "kangsticker.png"
                
                response = requests.get(url)
                with open(file_name, 'wb') as f:
                    f.write(response.content)
                
                im = Image.open(file_name)
                maxsize = (512, 512)
                if im.size[0] > maxsize[0] or im.size[1] > maxsize[1]:
                    im.thumbnail(maxsize, Image.LANCZOS)
                elif im.size[0] < maxsize[0] and im.size[1] < maxsize[1]:
                    scale = min(maxsize[0] / im.size[0], maxsize[1] / im.size[1])
                    new_size = (int(im.size[0] * scale), int(im.size[1] * scale))
                    im = im.resize(new_size, Image.LANCZOS)
                im.save(file_name, "PNG")
                
                msg.reply_photo(photo=open(file_name, 'rb'))
                bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    png_sticker=open(file_name, 'rb'),
                    emojis=sticker_emoji
                )
                msg.reply_text(
                    f"Sticker successfully added to [pack](t.me/addstickers/{packname})\nEmoji: {sticker_emoji}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except (OSError, ValueError) as e:
                msg.reply_text("I can only kang images from URLs.")
                print(e)
        
        else:
            msg.reply_text("Please reply to a sticker or provide an image URL to kang.")
    
    finally:
        if file_name and os.path.isfile(file_name):
            os.remove(file_name)


def makepack_internal(update, context, msg, user, emoji, packname, **sticker_params):
    bot = context.bot
    name = user.first_name[:50]
    
    try:
        bot.create_new_sticker_set(
            user_id=user.id,
            name=packname,
            title=f"{name}'s kang pack",
            emojis=emoji,
            **sticker_params
        )
        msg.reply_text(
            f"Sticker pack successfully created. Get it [here](t.me/addstickers/{packname})",
            parse_mode=ParseMode.MARKDOWN
        )
    except TelegramError as e:
        print(e)
        if e.message == "Sticker set name is already occupied":
            msg.reply_text(
                f"Your pack can be found [here](t.me/addstickers/{packname})",
                parse_mode=ParseMode.MARKDOWN
            )
        elif e.message == "Peer_id_invalid":
            msg.reply_text(
                "Contact me in PM first.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(text="Start", url=f"t.me/{bot.username}")
                ]])
            )
        else:
            msg.reply_text(f"Failed to create sticker pack: {e.message}")


__help__ = """
- /stickerid: Reply to a sticker to get its file ID.
- /getsticker: Reply to a sticker to upload its raw file (PNG or TGS). Video stickers (WebM) are not supported.
- /kang [emoji] [url]: Reply to a sticker or provide an image URL to add it to your pack. Supports static (PNG/WebP) and animated (TGS) stickers. Video stickers (WebM) are not supported.
"""

__mod_name__ = "Stickers"

STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid, run_async=True)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker, run_async=True)
KANG_HANDLER = DisableAbleCommandHandler("kang", kang, admin_ok=True, run_async=True)

dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)
dispatcher.add_handler(KANG_HANDLER)
