import html
import json
import random
import os
import io
from datetime import datetime
from typing import Optional, List
from random import randint
from time import sleep

import requests
import tg_bot.modules.helper_funcs.cas_api as cas
from telegram import Message, Chat, User, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html
from telegram.error import BadRequest
from contextlib import redirect_stdout
from cowsay import cow

from tg_bot import dispatcher, CallbackContext, OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, BAN_STICKER, INFOPIC
from tg_bot.__main__ import GDPR
from tg_bot.__main__ import STATS, USER_INFO, TOKEN
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.chat_status import user_admin, sudo_plus

RUN_STRINGS = (
    "Where do you think you're going?",
    "Huh? what? did they get away?",
    "ZZzzZZzz... Huh? what? oh, just them again, nevermind.",
    "Get back here!",
    "Not so fast...",
    "Look out for the wall!",
    "Don't leave me alone with them!!",
    "You run, you die.",
    "Jokes on you, I'm everywhere",
    "You're gonna regret that...",
    "You could also try /kickme, I hear that's fun.",
    "Go bother someone else, no-one here cares.",
    "You can run, but you can't hide.",
    "Is that all you've got?",
    "I'm behind you...",
    "You've got company!",
    "We can do this the easy way, or the hard way.",
    "You just don't get it, do you?",
    "Yeah, you better run!",
    "Please, remind me how much I care?",
    "I'd run faster if I were you.",
    "That's definitely the droid we're looking for.",
    "May the odds be ever in your favour.",
    "Famous last words.",
    "And they disappeared forever, never to be seen again.",
    "\"Oh, look at me! I'm so cool, I can run from a bot!\" - this person",
    "Yeah yeah, just tap /kickme already.",
    "Here, take this ring and head to Mordor while you're at it.",
    "Legend has it, they're still running...",
    "Unlike Harry Potter, your parents can't protect you from me.",
    "Fear leads to anger. Anger leads to hate. Hate leads to suffering. If you keep running in fear, you might "
    "be the next Vader.",
    "Multiple calculations later, I have decided my interest in your shenanigans is exactly 0.",
    "Legend has it, they're still running.",
    "Keep it up, not sure we want you here anyway.",
    "You're a wiza- Oh. Wait. You're not Harry, keep moving.",
    "NO RUNNING IN THE HALLWAYS!",
    "Hasta la vista, baby.",
    "Who let the dogs out?",
    "It's funny, because no one cares.",
    "Ah, what a waste. I liked that one.",
    "Frankly, my dear, I don't give a damn.",
    "My milkshake brings all the boys to yard... So run faster!",
    "You can't HANDLE the truth!",
    "A long time ago, in a galaxy far far away... Someone would've cared about that. Not anymore though.",
    "Hey, look at them! They're running from the inevitable banhammer... Cute.",
    "Han shot first. So will I.",
    "What are you running after, a white rabbit?",
    "As The Doctor would say... RUN!",
)

SLAP_TEMPLATES = (
    "{user1} {hits} {user2} with a {item}.",
    "{user1} {hits} {user2} in the face with a {item}.",
    "{user1} {hits} {user2} around a bit with a {item}.",
    "{user1} {throws} a {item} at {user2}.",
    "{user1} grabs a {item} and {throws} it at {user2}'s face.",
    "{user1} launches a {item} in {user2}'s general direction.",
    "{user1} starts slapping {user2} silly with a {item}.",
    "{user1} pins {user2} down and repeatedly {hits} them with a {item}.",
    "{user1} grabs up a {item} and {hits} {user2} with it.",
    "{user1} ties {user2} to a chair and {throws} a {item} at them.",
    "{user1} gave a friendly push to help {user2} learn to swim in lava.")

ITEMS = (
    "cast iron skillet",
    "large trout",
    "baseball bat",
    "cricket bat",
    "wooden cane",
    "nail",
    "printer",
    "shovel",
    "CRT monitor",
    "physics textbook",
    "toaster",
    "portrait of Richard Stallman",
    "television",
    "five ton truck",
    "roll of duct tape",
    "book",
    "laptop",
    "old television",
    "sack of rocks",
    "rainbow trout",
    "rubber chicken",
    "spiked bat",
    "fire extinguisher",
    "heavy rock",
    "chunk of dirt",
    "beehive",
    "piece of rotten meat",
    "bear",
    "ton of bricks",
)

THROW = (
    "throws",
    "flings",
    "chucks",
    "hurls",
)

HIT = (
    "hits",
    "whacks",
    "slaps",
    "smacks",
    "bashes",
)

GMAPS_LOC = "https://maps.googleapis.com/maps/api/geocode/json"
GMAPS_TIME = "https://maps.googleapis.com/maps/api/timezone/json"

FLASH_STRINGS = (
    "bootloop",
    "error 7",
    "zip corrupted",
    "battery died",
    "virus",
    "not enough space",
    "locked bootloader",
    "knox 0x0",
    "try again later",
    "yumi protection",
    "sdcard corrupted",
    "verizon locked carrier",
    "emmc died",
    "nusantara recovery not supported",
    "battery corruption",
    "failed to mount system",
    "failed to mount system_ext",
    "failed to mount product",
    "failed to mount vendor",
    "failed to mount partitions",
    "system is mounted as read-only",
    "system_ext is mounted as read-only",
    "product is mounted as read-only",
    "vendor is mounted as read-only",
    "beep bop... something wrong",
    "your opinion rejected",
)


def runs(update: Update, context: CallbackContext):
    bot = context.bot
    update.effective_message.reply_text(random.choice(RUN_STRINGS))


def slap(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    msg = update.effective_message  # type: Optional[Message]

    # reply to correct message
    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text

    # get user who sent message
    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(msg.from_user.first_name,
                                                   msg.from_user.id)

    user_id = extract_user(update.effective_message, args)
    if user_id == bot.id:
        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        if slapped_user.username:
            user2 = "@" + escape_markdown(slapped_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(slapped_user.first_name,
                                                   slapped_user.id)

    # if no target found, bot targets the sender
    else:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user

    temp = random.choice(SLAP_TEMPLATES)
    item = random.choice(ITEMS)
    hit = random.choice(HIT)
    throw = random.choice(THROW)

    repl = temp.format(user1=user1,
                       user2=user2,
                       item=item,
                       hits=hit,
                       throws=throw)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)


def get_id(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    user_id = extract_user(update.effective_message, args)
    if user_id:
        if update.effective_message.reply_to_message and update.effective_message.reply_to_message.forward_from:
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            update.effective_message.reply_text(
                "The original sender, {}, has an ID of `{}`.\nThe forwarder, {}, has an ID of `{}`."
                .format(escape_markdown(user2.first_name), user2.id,
                        escape_markdown(user1.first_name), user1.id),
                parse_mode=ParseMode.MARKDOWN)
        else:
            user = bot.get_chat(user_id)
            update.effective_message.reply_text("{}'s id is `{}`.".format(
                escape_markdown(user.first_name), user.id),
                                                parse_mode=ParseMode.MARKDOWN)
    else:
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == "private":
            update.effective_message.reply_text("Your id is `{}`.".format(
                chat.id),
                                                parse_mode=ParseMode.MARKDOWN)

        else:
            update.effective_message.reply_text(
                "This group's id is `{}`.".format(chat.id),
                parse_mode=ParseMode.MARKDOWN)


def info(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    msg = update.effective_message
    chat = update.effective_chat
    full = False

    # Check for full info flag
    if msg.text.find(" -f") != -1:
        full = True
        msg.text = msg.text.replace(" -f", "")
        args = [arg for arg in args if arg != "-f"]

    # Extract user ID
    user_id = extract_user(msg, args)
    if user_id:
        user = bot.get_chat(user_id)
    elif not msg.reply_to_message and not args:
        user = msg.sender_chat if msg.sender_chat else msg.from_user
    elif not msg.reply_to_message and (
            not args or
            (args and not args[0].startswith("@") and not args[0].isdigit() and
             not msg.parse_entities([MessageEntity.TEXT_MENTION]))):
        msg.reply_text("I can't extract a user from this.")
        return
    else:
        return

    # Initialize text for response
    is_chat = hasattr(user, 'type') and user.type != "private"
    text = f"<b>{'Chat' if is_chat else 'User'} Info</b>:\n"
    text += f"  <b>ID</b>: <code>{user.id}</code>\n"
    text += f"  <b>{'Title' if is_chat else 'First Name'}</b>: {user.title if is_chat else mention_html(user.id, user.first_name)}\n"

    if not is_chat:
        text += f"  <b>Last Name</b>: {html.escape(user.last_name or 'null')}\n"
    if user.username:
        text += f"  <b>Username</b>: @{html.escape(user.username)}\n"
    if is_chat:
        text += f"  <b>Chat Type</b>: {user.type.capitalize()}\n"

    # Get full user info if applicable
    if not is_chat:
        try:
            profile_pics = bot.get_user_profile_photos(user.id).total_count or "??"
            text += f"  <b>Profile Pics</b>: <code>{profile_pics}</code>\n"
        except BadRequest:
            pass
        text += f"  <b>User link</b>: {mention_html(user.id, 'here')}\n"
        if full:
            text += get_full_user_info(chat, user, bot)

    # Handle profile picture if INFOPIC is enabled
    if is_chat and INFOPIC:
        try:
            profile = bot.get_chat(user.id).photo
            _file = bot.get_file(profile["big_file_id"])
            _file.download(f"{user.id}.png")
            msg.reply_document(
                document=open(f"{user.id}.png", "rb"),
                caption=text,
                parse_mode=ParseMode.HTML,
            )
            os.remove(f"{user.id}.png")
        except (BadRequest, KeyError):
            msg.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    elif not is_chat and INFOPIC:
        try:
            profile = context.bot.get_user_profile_photos(user.id).photos[0][-1]
            _file = bot.get_file(profile["file_id"])
            _file.download(f"{user.id}.png")
            msg.reply_document(
                document=open(f"{user.id}.png", "rb"),
                caption=text,
                parse_mode=ParseMode.HTML,
            )
            os.remove(f"{user.id}.png")
        except (IndexError, BadRequest):
            msg.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    else:
        msg.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

def get_full_user_info(chat, user, bot) -> str:
    text = ""
    # User level checks
    if user.id == OWNER_ID:
        text += f"  <b>User level</b>: <code>Owner</code>\n"
    elif user.id in DEV_USERS:
        text += f"  <b>User level</b>: <code>Developer</code>\n"
    elif user.id in SUDO_USERS:
        text += f"  <b>User level</b>: <code>Sudo</code>\n"
    elif user.id in SUPPORT_USERS:
        text += f"  <b>User level</b>: <code>Support</code>\n"
    elif user.id in WHITELIST_USERS:
        text += f"  <b>User level</b>: <code>Whitelist</code>\n"

    # Chat member status
    try:
        user_member = chat.get_member(user.id)
        status = user_member.status
        if status == "left":
            text += f"  <b>Presence</b>: <code>Not here</code>\n"
        elif status == "kicked":
            text += f"  <b>Presence</b>: <code>Banned</code>\n"
        elif status == "member":
            text += f"  <b>Presence</b>: <code>Detected</code>\n"
        elif status in ("administrator", "creator"):
            text += f"  <b>Presence</b>: <code>Admin</code>\n"
            if user_member.custom_title:
                text += f"  <b>Title</b>: <code>{user_member.custom_title}</code>\n"
    except BadRequest:
        pass

    text += f"  <b>CAS Banned</b>: <code>{cas.banchecker(user.id)}</code>\n"

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += f"  {mod_info}\n"
    return text


@user_admin
def ginfo(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        msg.reply_text("Please reply this command in group!")
    else:
        text = "<b>Chat info:</b>" \
               "\nㅤ<b>Title</b>: <code>{}</code>".format(update.effective_chat.title)

        if chat.username:
            text += "\nㅤ<b>Username</b>: @{}".format(chat.username)

        text += "\nㅤ<b>ID</b>: <code>{}</code>".format(chat.id)

        if chat.type in [chat.SUPERGROUP, chat.CHANNEL]:
            bot_member = chat.get_member(bot.id)
            if bot_member.can_invite_users:
                invitelink = bot.exportChatInviteLink(chat.id)
                text += f"\nㅤ<b>Invitelink</b>: {invitelink}"

        if chat.type == "group":
            text += f"\nㅤ<b>Type</b>: <code>Group</code>"

        if chat.type == "supergroup":
            text += f"\nㅤ<b>Type</b>: <code>Supergroup</code>"

        admins_count = bot.getChatAdministrators(chat.id)
        status = chat.get_member(user.id)
        if status == "administrator":
            text += "\nㅤ<b>Total Admins</b>: <code>{}</code>".format(
                len(admins_count))
        if status == "creator":
            text += "\n  Creator: {}".format(
                mention_html(user.id, user.first_name))

        text += "\nㅤ<b>Total Members</b>: <code>{}</code>".format(
            chat.get_member_count(user.id))

        msg.reply_text(text,
                       disable_web_page_preview=True,
                       parse_mode=ParseMode.HTML)


def get_time(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    location = " ".join(args)
    if location.lower() == bot.first_name.lower():
        update.effective_message.reply_text(
            "Its always banhammer time for me!")
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)
        return

    res = requests.get(GMAPS_LOC, params=dict(address=location))

    if res.status_code == 200:
        loc = json.loads(res.text)
        if loc.get('status') == 'OK':
            lat = loc['results'][0]['geometry']['location']['lat']
            long = loc['results'][0]['geometry']['location']['lng']

            country = None
            city = None

            address_parts = loc['results'][0]['address_components']
            for part in address_parts:
                if 'country' in part['types']:
                    country = part.get('long_name')
                if 'administrative_area_level_1' in part['types'] and not city:
                    city = part.get('long_name')
                if 'locality' in part['types']:
                    city = part.get('long_name')

            if city and country:
                location = "{}, {}".format(city, country)
            elif country:
                location = country

            timenow = int(datetime.utcnow().timestamp())
            res = requests.get(GMAPS_TIME,
                               params=dict(location="{},{}".format(lat, long),
                                           timestamp=timenow))
            if res.status_code == 200:
                offset = json.loads(res.text)['dstOffset']
                timestamp = json.loads(res.text)['rawOffset']
                time_there = datetime.fromtimestamp(timenow + timestamp +
                                                    offset).strftime(
                                                        "%H:%M:%S on %A %d %B")
                update.message.reply_text("It's {} in {}".format(
                    time_there, location))


@sudo_plus
def echo(update: Update, context: CallbackContext):
    bot = context.bot
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)
    try:
        message.delete()
    except BadRequest:
        pass


@sudo_plus
def recho(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError as excp:
        message.reply_text("Please give me a chat ID.")
    to_send = " ".join(args)
    if len(to_send) >= 2:
        try:
            bot.sendMessage(int(chat_id), str(to_send))
        except BadRequest:
            pass


def flash(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    string = ""

    if message.reply_to_message:
        if message.reply_to_message.text:
            string = message.reply_to_message.text.lower().replace(" ", "_")

    if args:
        string = " ".join(args).replace(" ", "_").lower()

    if not string:
        message.reply_text("Usage: `/flash <text>`",
                           parse_mode=ParseMode.MARKDOWN)
        return

    if len(string) > 30:
        message.reply_text(
            "Your message exceeded limit.\nShortening it to 30 characters.")

    if message.reply_to_message:
        flash = message.reply_to_message.reply_text("<code>Flashing...</code>",
                                                    parse_mode=ParseMode.HTML)
        sleep(randint(1, 3))
        flash.edit_text(
            f"Flashing <code>{string[:30]}.zip</code> succesfully failed!\nBecause: <code>{random.choice(FLASH_STRINGS)}</code>",
            parse_mode=ParseMode.HTML)
    else:
        flash = message.reply_text("<code>Flashing...</code>",
                                   parse_mode=ParseMode.HTML)
        sleep(randint(1, 3))
        flash.edit_text(
            f"Flashing <code>{string[:30]}.zip</code> succesfully failed!\nBecause: <code>{random.choice(FLASH_STRINGS)}</code>",
            parse_mode=ParseMode.HTML)


def cowsay(update: Update, context: CallbackContext):
    with io.StringIO() as buf, redirect_stdout(buf):
        try:
            cow(update.message.text.split(' ', 1)[1])
        except IndexError:
            update.message.reply_text(f"Usage: `/cowsay bow-bow or <text>`",
                                      parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text(f"`{buf.getvalue()}`",
                                      parse_mode=ParseMode.MARKDOWN)


def gdpr(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    update.effective_message.reply_text("Deleting identifiable data...")
    for mod in GDPR:
        mod.__gdpr__(update.effective_user.id)

    update.effective_message.reply_text(
        "Your personal data has been deleted.\n\nNote that this will not unban "
        "you from any chats, as that is telegram data, not Marie data. "
        "Flooding, warns, and gbans are also preserved, as of "
        "[this](https://ico.org.uk/for-organisations/guide-to-the-general-data-protection-regulation-gdpr/individual-rights/right-to-erasure/), "
        "which clearly states that the right to erasure does not apply "
        "\"for the performance of a task carried out in the public interest\", as is "
        "the case for the aforementioned pieces of data.",
        parse_mode=ParseMode.MARKDOWN)


MARKDOWN_HELP = """
Markdown is a very powerful formatting tool supported by telegram. {} has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.
- <code>_italic_</code>: wrapping text with '_' will produce italic text
- <code>*bold*</code>: wrapping text with '*' will produce bold text
- <code>`code`</code>: wrapping text with '`' will produce monospaced text, also known as 'code'
- <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
EG: <code>[test](example.com)</code>
- <code>[buttontext](buttonurl:someURL)</code>: this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
EG: <code>[This is a button](buttonurl:example.com)</code>
If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.
Keep in mind that your message <b>MUST</b> contain some text other than just a button!
""".format(dispatcher.bot.first_name)


def markdown_help(update: Update, context: CallbackContext):
    bot = context.bot
    update.effective_message.reply_text(MARKDOWN_HELP,
                                        parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Try forwarding the following message to me, and you'll see!")
    update.effective_message.reply_text(
        "/save test This is a markdown test. _italics_, *bold*, `code`, "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)")


@sudo_plus
def stats(update: Update, context: CallbackContext):
    bot = context.bot
    update.effective_message.reply_text(
        "Current stats:\n" + "\n".join([mod.__stats__() for mod in STATS]))


# /ip is for private use
__help__ = """
 - /id: get the current group id. If used by replying to a message, gets that user's id.
 - /runs: reply a random string from an array of replies.
 - /slap: slap a user, or get slapped if not a reply.
 - /info: get information about a user.
 - /info -f: get full information about a user.
 - /flash: <text>: flashes your choosed strings.
 - /gdpr: deletes your information from the bot's database. Private chats only.
 - /markdownhelp: quick summary of how markdown works in telegram - can only be called in private chats.
"""

__mod_name__ = "Misc"

ID_HANDLER = DisableAbleCommandHandler("id", get_id, run_async=True)
TIME_HANDLER = CommandHandler("time", get_time, run_async=True)
RUNS_HANDLER = DisableAbleCommandHandler("runs", runs, run_async=True)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap, run_async=True)
INFO_HANDLER = DisableAbleCommandHandler("info", info, run_async=True)
GINFO_HANDLER = DisableAbleCommandHandler("ginfo", ginfo, run_async=True)
FLASH_HANDLER = DisableAbleCommandHandler("flash", flash, run_async=True)
COWSAY_HANDLER = DisableAbleCommandHandler("cowsay", cowsay, run_async=True)
ECHO_HANDLER = CommandHandler("echo", echo, run_async=True)
RECHO_HANDLER = CommandHandler("recho", recho, run_async=True)
MD_HELP_HANDLER = CommandHandler("markdownhelp",
                                 markdown_help,
                                 filters=Filters.private,
                                 run_async=True)
STATS_HANDLER = CommandHandler("stats", stats, run_async=True)
GDPR_HANDLER = CommandHandler("gdpr",
                              gdpr,
                              filters=Filters.private,
                              run_async=True)

dispatcher.add_handler(ID_HANDLER)
# dispatcher.add_handler(TIME_HANDLER)
dispatcher.add_handler(RUNS_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(GINFO_HANDLER)
dispatcher.add_handler(FLASH_HANDLER)
dispatcher.add_handler(COWSAY_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(RECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(GDPR_HANDLER)
