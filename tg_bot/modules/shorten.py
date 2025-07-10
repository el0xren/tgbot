import logging
import ipaddress
import urllib.parse
from typing import List, Tuple

import requests
from telegram import Update, MessageEntity
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext

from tg_bot import dispatcher
from tg_bot.modules.sql.shorten_sql import is_shortening_enabled, set_shortening_enabled
from tg_bot.modules.helper_funcs.chat_status import user_admin

LOGGER = logging.getLogger(__name__)

SHORTENER_DOMAINS = {
    "bit.ly",
    "t.co",
    "tinyurl.com",
    "goo.gl",
    "is.gd",
    "cutt.ly",
    "rb.gy",
    "shrtco.de",
    "shorturl.at",
    "rebrand.ly",
}

COMMON_TLDS = {
    "com",
    "org",
    "net",
    "io",
    "ai",
    "co",
    "edu",
    "gov",
    "mil",
    "biz",
    "info",
    "uk",
    "ca",
    "de",
    "fr",
    "jp",
    "cn",
    "ru",
    "br",
    "au",
    "in",
}


def extract_domain(url: str) -> str:
    try:
        hostname = urllib.parse.urlparse(url).hostname or ""
        return hostname.lstrip("www.").lower()
    except Exception:
        return ""


def is_private_address(url: str) -> bool:
    try:
        host = urllib.parse.urlparse(url).hostname or ""
        if host in ("localhost", ) or host.endswith(".local"):
            return True
        ip = ipaddress.ip_address(host)
        return ip.is_private
    except Exception:
        return False


def is_valid_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        domain_parts = parsed.hostname.lower().split(".")
        if len(domain_parts) < 2:
            return False
        if domain_parts[-1] not in COMMON_TLDS:
            return False
        return True
    except Exception:
        return False


def shorten_url(url: str) -> str:
    try:
        response = requests.get(
            "https://is.gd/create.php",
            params={
                "format": "simple",
                "url": url
            },
            timeout=5,
        )
        shortened = response.text.strip()
        if shortened.startswith("https://"):
            shortened = shortened[len("https://"):]
        return shortened if response.ok and shortened else url
    except requests.RequestException as e:
        LOGGER.warning("Shortening failed for %s: %s", url, e)
        return url


@user_admin
def cmd_toggle_shortening(update: Update, ctx: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == "private":
        return msg.reply_text("Use this command in groups only.")

    args = ctx.args
    if not args:
        current = is_shortening_enabled(chat.id)
        return msg.reply_text(
            f"URL shortening is currently <b>{'enabled' if current else 'disabled'}</b>.",
            parse_mode="HTML",
        )

    choice = args[0].lower()
    if choice not in ("enable", "disable"):
        return msg.reply_text("Usage: /shortening <enable|disable>")

    enabled = choice == "enable"
    set_shortening_enabled(chat.id, enabled)
    msg.reply_text(f"URL shortening <b>{choice}d</b>.", parse_mode="HTML")


def cmd_shorten(update: Update, ctx: CallbackContext) -> None:
    msg = update.effective_message
    if not ctx.args:
        return msg.reply_text("Usage: /shorten <url>", parse_mode="HTML")

    url = ctx.args[0]
    domain = extract_domain(url)

    if not is_valid_url(url):
        return msg.reply_text("Invalid URL.", parse_mode="HTML")

    if is_private_address(url):
        return msg.reply_text("Refusing to shorten local/private addresses.",
                              parse_mode="HTML")

    if domain in SHORTENER_DOMAINS:
        return msg.reply_text("Already shortened URL.", parse_mode="HTML")

    waiting = msg.reply_text("Shortening...")
    short = shorten_url(url)

    if short == url:
        return waiting.edit_text("Failed to shorten the URL.",
                                 parse_mode="HTML")

    waiting.edit_text(
        f"<b>Original:</b> {url}\n<b>Shortened:</b> {short}",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


def auto_shorten(update: Update, ctx: CallbackContext) -> None:
    msg = update.effective_message
    chat = update.effective_chat

    if not is_shortening_enabled(chat.id) or not msg.entities:
        return

    seen: set[str] = set()
    shortened: List[Tuple[str, str]] = []

    for entity in msg.entities:
        url = None

        if entity.type == MessageEntity.URL:
            url = msg.text[entity.offset:entity.offset + entity.length]
        elif entity.type == MessageEntity.TEXT_LINK:
            url = entity.url

        if not url or url in seen:
            continue
        seen.add(url)

        domain = extract_domain(url)
        if domain in SHORTENER_DOMAINS:
            continue
        if not is_valid_url(url) or is_private_address(url):
            continue

        short = shorten_url(url)
        if short != url:
            shortened.append((url, short))

    if shortened:
        reply = "\n".join(
            f"<b>Shortened:</b> {short}" for _, short in shortened)
        try:
            msg.reply_text(reply,
                           parse_mode="HTML",
                           disable_web_page_preview=True)
        except Exception as e:
            LOGGER.error("Error sending shortened URLs: %s", e)


dispatcher.add_handler(CommandHandler("shorten", cmd_shorten))
dispatcher.add_handler(CommandHandler("shortening", cmd_toggle_shortening))
dispatcher.add_handler(
    MessageHandler(
        Filters.text & Filters.chat_type.groups
        & (Filters.entity(MessageEntity.URL) | Filters.entity(MessageEntity.TEXT_LINK)),
        auto_shorten),
        group=0,
)
