import re
import requests
import ipaddress
import urllib.parse
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from tg_bot import dispatcher
from tg_bot.modules.sql import utilities_sql as sql
from tg_bot.modules.helper_funcs.chat_status import user_admin

SHORTENER_DOMAINS = {
    "bit.ly",
    "t.co",
    "tinyurl.com",
    "goo.gl",
    "is.gd",
    "shorturl.at",
    "cutt.ly",
    "rb.gy",
    "rebrand.ly",
    "shrtco.de",
}

COMMON_TLDS = {
    "com",
    "org",
    "net",
    "edu",
    "gov",
    "mil",
    "biz",
    "info",
    "io",
    "co",
    "ai",
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

URL_REGEX = r"^(?:https?://)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[-a-zA-Z0-9._~:/?#[\]@!$&\'()*+,;=]*)?$"


def validate_url(url: str) -> bool:
    try:
        test_url = url if url.startswith(
            ("http://", "https://")) else "https://" + url

        if not re.match(
                URL_REGEX, test_url if test_url.startswith(
                    ("http://", "https://")) else url):
            return False

        parsed = urllib.parse.urlparse(test_url)
        if not parsed.netloc:
            return False

        domain = parsed.netloc.lower()
        domain_parts = domain.split(".")

        if domain_parts[0] == "www":
            domain_parts = domain_parts[1:]

        if len(domain_parts) < 2 or any(not part for part in domain_parts):
            return False

        for part in domain_parts[:-1]:
            if not re.match(r"^[a-zA-Z0-9-]+$", part):
                return False
            if len(part) > 63:
                return False
            if len(part) > 10 and not any(c in "aeiou" for c in part.lower()):
                return False

        tld = domain_parts[-1]
        if tld not in COMMON_TLDS:
            return False

        if len(domain_parts) > 2:
            for part in domain_parts[:-1]:
                if part in COMMON_TLDS:
                    return False

        return True
    except ValueError:
        return False


@user_admin
def shortening_toggle(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    args = context.args

    if update.effective_chat.type == "private":
        update.message.reply_text(
            "This command can only be used in groups, not in private messages.",
            parse_mode="HTML",
        )
        return

    if not args:
        is_enabled = sql.is_shortening_enabled(chat_id)
        status = "enabled" if is_enabled else "disabled"
        update.message.reply_text(
            f"URL shortening is currently <b>{status}</b> for this chat.",
            parse_mode="HTML",
        )
        return

    command = args[0].lower()
    if command == "enable":
        if sql.is_shortening_enabled(chat_id):
            update.message.reply_text(
                "URL shortening is already <b>enabled</b> for this chat.",
                parse_mode="HTML",
            )
        else:
            sql.set_shortening_enabled(chat_id, True)
            update.message.reply_text(
                "URL shortening <b>enabled</b> for this chat.",
                parse_mode="HTML")
    elif command == "disable":
        if not sql.is_shortening_enabled(chat_id):
            update.message.reply_text(
                "URL shortening is already <b>disabled</b> for this chat.",
                parse_mode="HTML",
            )
        else:
            sql.set_shortening_enabled(chat_id, False)
            update.message.reply_text(
                "URL shortening <b>disabled</b> for this chat.",
                parse_mode="HTML")
    else:
        update.message.reply_text(
            "Usage: /shortening [<b>enable</b>|<b>disable</b>]",
            parse_mode="HTML")


def extract_domain(url: str) -> str:
    try:
        test_url = url if url.startswith(
            ("http://", "https://")) else "https://" + url
        parsed = urllib.parse.urlparse(test_url)
        domain = parsed.netloc.lower()
        return domain[4:] if domain.startswith("www.") else domain
    except ValueError:
        return ""


def is_local_or_private(url: str) -> bool:
    try:
        test_url = url if url.startswith(
            ("http://", "https://")) else "https://" + url
        parsed = urllib.parse.urlparse(test_url)
        domain = parsed.netloc.split(":")[0].lower()

        if not domain or domain == "localhost" or domain.endswith(".local"):
            return True

        try:
            ip = ipaddress.ip_address(domain)
            return ip.is_private
        except ValueError:
            return False
    except ValueError:
        return True


def shorten_url(url: str) -> str:
    if not validate_url(url):
        return url

    test_url = url if url.startswith(
        ("http://", "https://")) else "https://" + url
    try:
        response = requests.get(
            "https://is.gd/create.php",
            params={
                "format": "simple",
                "url": test_url
            },
            timeout=5,
        )
        if response.ok and response.text.startswith("http"):
            return response.text
        return url
    except requests.RequestException as e:
        print(f"Error shortening {url}: {e}")
        return url


def shorten_command(update: Update, context: CallbackContext) -> None:
    message = update.effective_message

    if not context.args:
        message.reply_text(
            "Please provide a URL to shorten.\nUsage: /shorten <url>",
            parse_mode="HTML")
        return

    url = context.args[0]

    if is_local_or_private(url):
        message.reply_text("Cannot shorten local or private IP addresses.",
                           parse_mode="HTML")
        return

    domain = extract_domain(url)
    if not domain:
        message.reply_text("Invalid URL format.", parse_mode="HTML")
        return

    if domain in SHORTENER_DOMAINS:
        message.reply_text("This URL is already from a shortening service.",
                           parse_mode="HTML")
        return

    if not validate_url(url):
        message.reply_text("Invalid URL. Please provide a valid URL.",
                           parse_mode="HTML")
        return

    status_msg = message.reply_text("Shortening URL...")

    shortened = shorten_url(url)

    if shortened != url:
        status_msg.edit_text(
            f"<b>Original</b>: {url}\n<b>Shortened</b>: {shortened}",
            disable_web_page_preview=True,
            parse_mode="HTML",
        )
    else:
        status_msg.edit_text("Failed to shorten this URL.", parse_mode="HTML")


def shorten_links(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    chat_id = update.effective_chat.id

    if not message or not message.text or not sql.is_shortening_enabled(
            chat_id):
        return

    urls = []
    for entity in message.entities:
        if entity.type == "url":
            url = message.text[entity.offset:entity.offset + entity.length]
            urls.append(url)

    if not urls:
        return

    status_msg = message.reply_text("Link detected, shortening...")

    shortened_map = {}
    invalid_urls = []
    valid_urls_count = 0

    for url in set(urls):
        if is_local_or_private(url):
            invalid_urls.append(url)
            continue

        domain = extract_domain(url)
        if not domain or domain in SHORTENER_DOMAINS:
            invalid_urls.append(url)
            continue

        if not validate_url(url):
            invalid_urls.append(url)
            continue

        shortened = shorten_url(url)
        if shortened != url:
            shortened_map[url] = shortened
            valid_urls_count += 1
        else:
            invalid_urls.append(url)

    if valid_urls_count > 0:
        result_text = ""

        if valid_urls_count == 1:
            original = next(iter(shortened_map.keys()))
            shortened = shortened_map[original]
            result_text = f"<b>Original</b>: {original}\n<b>Shortened</b>: {shortened}"
        else:
            result_text = "<b>Shortened Links</b>:\n\n"
            for original, short in shortened_map.items():
                result_text += (
                    f"<b>Original</b>: {original}\n<b>Shortened</b>: {short}\n\n"
                )

        try:
            status_msg.edit_text(
                result_text,
                disable_web_page_preview=True,
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"Failed to edit message: {e}")
            try:
                status_msg.delete()
            except Exception:
                pass
    else:
        try:
            if invalid_urls:
                invalid_list = "\n".join(f"- {url}" for url in invalid_urls)
                status_msg.edit_text(
                    f"No valid links to shorten. Invalid or private links:\n{invalid_list}",
                    disable_web_page_preview=True,
                )
            else:
                status_msg.edit_text(
                    "No valid links to shorten.",
                    disable_web_page_preview=True,
                )
        except Exception as e:
            print(f"Failed to edit message with invalid links: {e}")


__help__ = """
*Admin only:*
 - /shortening <enable/disable>: Without args it will check if it's enabled or disabled in chat \
else it will enable or disable shortening in the chat. Only works in groups, not in private messages.

*For all users:*
 - /shorten <url>: Manually shorten a URL (works in private messages and groups regardless of settings).
"""

__mod_name__ = "Utilities"

SHORTENING_HANDLER = CommandHandler("shortening", shortening_toggle)
SHORTEN_COMMAND_HANDLER = CommandHandler("shorten", shorten_command)
SHORTEN_LINK_HANDLER = MessageHandler(Filters.text & Filters.chat_type.groups,
                                      shorten_links)

dispatcher.add_handler(SHORTENING_HANDLER)
dispatcher.add_handler(SHORTEN_COMMAND_HANDLER)
dispatcher.add_handler(SHORTEN_LINK_HANDLER)
