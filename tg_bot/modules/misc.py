import html
import json
import random
from time import sleep
from typing import Optional, List
from random import randint
from contextlib import redirect_stdout
import io

import requests
from telegram import Message, Update, Bot, MessageEntity, ParseMode
from telegram.ext import CommandHandler, run_async, Filters, CallbackContext
from telegram.error import BadRequest, TelegramError
from telegram.utils.helpers import escape_markdown
from cowsay import cow

from tg_bot import dispatcher, SUDO_USERS, BAN_STICKER
from tg_bot.__main__ import GDPR, STATS, TOKEN
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.chat_status import sudo_plus

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
    msg = update.effective_message

    from_user = msg.from_user
    if from_user.username:
        curr_user = f"@{escape_markdown(from_user.username)}"
    else:
        curr_user = f"[{escape_markdown(from_user.first_name)}](tg://user?id={from_user.id})"

    user_id = extract_user(msg, args)

    if user_id and user_id != bot.id:
        target_user = bot.get_chat(user_id)
        if target_user.username:
            target = f"@{escape_markdown(target_user.username)}"
        else:
            target = f"[{escape_markdown(target_user.first_name)}](tg://user?id={target_user.id})"
        user1 = curr_user
        user2 = target
    else:
        user1 = f"[{escape_markdown(bot.first_name)}](tg://user?id={bot.id})"
        user2 = curr_user

    text = random.choice(SLAP_TEMPLATES).format(
        user1=user1,
        user2=user2,
        item=random.choice(ITEMS),
        hits=random.choice(HIT),
        throws=random.choice(THROW)
    )

    if msg.reply_to_message:
        msg.reply_to_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        msg.chat.send_message(text, parse_mode=ParseMode.MARKDOWN)


def get_id(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    user_id = extract_user(message, args)

    if user_id:
        if message.reply_to_message and message.reply_to_message.forward_from:
            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from
            message.reply_text(
                "The original sender, {}, has an ID of `{}`.\nThe forwarder, {}, has an ID of `{}`.".format(
                    escape_markdown(user2.first_name), user2.id,
                    escape_markdown(user1.first_name), user1.id),
                parse_mode=ParseMode.MARKDOWN)
        else:
            user = bot.get_chat(user_id)
            message.reply_text(
                "{}'s ID is `{}`.".format(
                    escape_markdown(user.first_name),
                    user.id),
                parse_mode=ParseMode.MARKDOWN)
    else:
        chat = update.effective_chat
        from_user = message.from_user
        message.reply_text(
            "{}'s ID: `{}`\nChat ID: `{}`\nMessage ID: `{}`".format(
                escape_markdown(from_user.first_name),
                from_user.id,
                chat.id,
                message.message_id),
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

    try:
        is_afk, reason = sql.check_afk_status(user.id)
        if is_afk:
            text += f"  <b>AFK</b>: Yes\n"
            if reason and reason.strip():
                text += f"    <b>Reason</b>: <code>{html.escape(reason)}</code>\n"
    except (IndexError, TypeError):
        pass

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


def permissions(update: Update, context: CallbackContext):
    """Command handler to display user info and permissions in a chat."""
    chat = update.effective_chat
    user = update.effective_user  # Default to the user who sent the command

    # Optionally extract user from reply or arguments
    if update.effective_message.reply_to_message:
        user = update.effective_message.reply_to_message.from_user
    elif context.args:
        user_id = extract_user(update.effective_message, context.args)
        if user_id:
            try:
                user = context.bot.get_chat(user_id)
            except BadRequest:
                update.effective_message.reply_text("Could not find that user.")
                return
        else:
            update.effective_message.reply_text("I can't extract a user from this.")
            return

    # Generate user info and admin permissions
    bot = context.bot
    text = "<b>User Info:</b>\n"
    text += f"  User: {html.escape(user.first_name)}\n"
    text += f"  ID: <code>{user.id}</code>\n"

    # Permissions section
    try:
        member = bot.get_chat_member(chat.id, user.id)
        if member.status in ("administrator", "creator"):
            text += "\n<b>Permissions:</b>\n"
            for perm in AdminPerms:
                has_perm = getattr(member, perm.value, False)
                perms_name = perm.name.replace('_', ' ').title()
                text += f" • {perms_name}: <code>{str(has_perm)}</code>\n"
        else:
            text += "\n<b>Permissions:</b> <code>Not an admin</code>\n"
    except BadRequest as e:
        text += f"\n<b>Error:</b> <code>Could not retrieve permissions: {e}</code>\n"

    # Send response
    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@user_admin
def ginfo(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        return msg.reply_text("This command can only be used in a group or channel.")

    try:
        bot_member = chat.get_member(bot.id)
    except (BadRequest, Unauthorized):
        return msg.reply_text("Could not retrieve bot permissions.")

    text = f"<b>Chat Info</b>\n"
    text += f"ㅤ<b>Title:</b> <code>{chat.title}</code>\n"
    text += f"ㅤ<b>ID:</b> <code>{chat.id}</code>\n"

    if chat.username:
        text += f"ㅤ<b>Username:</b> @{chat.username}\n"

    if chat.type == chat.SUPERGROUP:
        text += "ㅤ<b>Type:</b> Supergroup\n"
    elif chat.type == chat.GROUP:
        text += "ㅤ<b>Type:</b> Group\n"
    elif chat.type == chat.CHANNEL:
        text += "ㅤ<b>Type:</b> Channel\n"

    if bot_member.can_invite_users:
        try:
            invite_link = bot.exportChatInviteLink(chat.id)
            text += f"ㅤ<b>Invite Link:</b> {invite_link}\n"
        except BadRequest:
            pass

    try:
        admins = bot.getChatAdministrators(chat.id)
        text += f"ㅤ<b>Total Admins:</b> {len(admins)}\n"
    except:
        pass

    try:
        for admin in admins:
            if admin.status == "creator":
                text += f"ㅤ<b>Creator:</b> {mention_html(admin.user.id, admin.user.full_name)}\n"
                break
    except:
        pass

    try:
        members = bot.get_chat_member_count(chat.id)
        text += f"ㅤ<b>Total Members:</b> {members}\n"
    except:
        pass

    try:
        if hasattr(chat, "slow_mode_delay") and chat.slow_mode_delay:
            text += f"ㅤ<b>Slowmode:</b> {chat.slow_mode_delay} sec\n"
    except:
        pass

    if chat.sticker_set_name:
        text += f"ㅤ<b>Sticker Set:</b> <code>{chat.sticker_set_name}</code>\n"

    msg.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


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
    message = update.effective_message
    args = context.args

    try:
        if not args:
            message.reply_text("Usage: /echo <text>")
            return

        reply_text = " ".join(args).strip()

        if not reply_text:
            message.reply_text("Usage: /echo <text>")
            return

        if message.reply_to_message:
            message.reply_to_message.reply_text(reply_text)
        else:
            message.reply_text(reply_text, quote=False)

    except (BadRequest, TelegramError) as e:
        message.reply_text(f"Failed to send message: {e.message}")
    finally:
        try:
            message.delete()
        except BadRequest:
            pass

@sudo_plus
def recho(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args

    try:
        if len(args) < 2:
            message.reply_text("Usage: /recho <chat_id> <text>")
            return

        chat_id = int(args[0])
        to_send = " ".join(args[1:]).strip()

        if not to_send:
            message.reply_text("Nothing to send.")
            return

        context.bot.send_message(chat_id=chat_id, text=to_send)
        
        if chat.type == "private":
            message.reply_text("Message sent.")

    except ValueError:
        message.reply_text("Invalid chat ID.")
    except (BadRequest, TelegramError) as e:
        message.reply_text(f"Failed to send message: {e.message}")
    finally:
        if chat.type != "private":
            try:
                message.delete()
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

    escaped_string = html.escape(string[:30])

    if len(string) > 30:
        message.reply_text(
            "Your message exceeded limit.\nShortening it to 30 characters.")

    if message.reply_to_message:
        flash = message.reply_to_message.reply_text("<code>Flashing...</code>",
                                                    parse_mode=ParseMode.HTML)
        sleep(randint(1, 3))
        flash.edit_text(
            f"Flashing <code>{escaped_string}.zip</code> succesfully failed!\nBecause: <code>{random.choice(FLASH_STRINGS)}</code>",
            parse_mode=ParseMode.HTML)
    else:
        flash = message.reply_text("<code>Flashing...</code>",
                                   parse_mode=ParseMode.HTML)
        sleep(randint(1, 3))
        flash.edit_text(
            f"Flashing <code>{escaped_string}.zip</code> succesfully failed!\nBecause: <code>{random.choice(FLASH_STRINGS)}</code>",
            parse_mode=ParseMode.HTML)


def cowsay(update: Update, context: CallbackContext) -> None:
    if not update.message or not update.message.text:
        return

    try:
        args = update.message.text.split(' ', 1)
        
        if len(args) < 2 or not args[1].strip():
            update.message.reply_text(
                "Usage: `/cowsay <text>`\nExample: `/cowsay bow-bow`",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return

        with io.StringIO() as buf, redirect_stdout(buf):
            cow(args[1].strip())
            output = buf.getvalue()
        
        escaped_output = output.replace('`', '\\`').replace('_', '\\_')
        
        update.message.reply_text(
            f"```{escaped_output}```",
            parse_mode=ParseMode.MARKDOWN_V2
        )

    except Exception as e:
        update.message.reply_text(
            f"Error: Something went wrong. Please try again.\nDetails: {str(e)}",
            parse_mode=ParseMode.MARKDOWN_V2
        )


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
 - /permissions: display a user's permissions in the current chat.
 - /ginfo: get information about the current group.
 - /flash <text>: flashes your chosen strings.
 - /cowsay <text>: displays the text in a fun ASCII cow format.
 - /echo <text>: echoes the provided text in the current chat.
 - /recho <chat_id> <text>: sends the provided text to the specified chat ID.
 - /stats: displays bot statistics (sudo users only).
 - /gdpr: deletes your information from the bot's database. Private chats only.
 - /markdownhelp: quick summary of how markdown works in Telegram - can only be called in private chats.
"""

__mod_name__ = "Misc"

ID_HANDLER = DisableAbleCommandHandler("id", get_id, run_async=True)
TIME_HANDLER = CommandHandler("time", get_time, run_async=True)
RUNS_HANDLER = DisableAbleCommandHandler("runs", runs, run_async=True)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap, run_async=True)
INFO_HANDLER = DisableAbleCommandHandler("info", info, run_async=True)
PERMISSIONS_HANDLER = DisableAbleCommandHandler("permissions", permissions, run_async=True)
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
dispatcher.add_handler(PERMISSIONS_HANDLER)
dispatcher.add_handler(GINFO_HANDLER)
dispatcher.add_handler(FLASH_HANDLER)
dispatcher.add_handler(COWSAY_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(RECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(GDPR_HANDLER)
