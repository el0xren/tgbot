import os
import re
import time
import tempfile
import shutil
import requests
import logging
from urllib.parse import urljoin
from html import escape
from bs4 import BeautifulSoup
from requests import get, HTTPError
from ujson import loads
from datetime import datetime
from typing import Optional, List, Tuple

from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext, Filters
from tg_bot import dispatcher

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

BASE_URL = "https://www.gsmarena.com"

HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Accept":
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

SEARCH_ENDPOINTS = [
    "/results.php3?sQuickSearch=yes&sName=",
    "/res.php3?sSearch=",
    "/search.php3?sSearch=",
]

SELECTORS = [
    "div.makers ul li a",
    "ul#results-list li a",
    "div#review-body a",
    "div.search-results a",
    'div.results a[href*=".php"]',
    "div.phone-list a",
    'a[href*=".php"]',
]

SPEC_CATEGORIES = [
    "Network",
    "Network.Technology",
    "Launch",
    "Launch.Announced",
    "Launch.Status",
    "Body",
    "Body.Dimensions",
    "Body.Weight",
    "Body.Build",
    "Display",
    "Display.Type",
    "Display.Size",
    "Display.Resolution",
    "Platform",
    "Platform.OS",
    "Platform.Chipset",
    "Platform.CPU",
    "Memory",
    "Memory.Internal",
    "Memory.Card slot",
    "Main Camera",
    "Main Camera.Single",
    "Main Camera.Dual",
    "Main Camera.Triple",
    "Main Camera.Quad",
    "Main Camera.Features",
    "Selfie Camera",
    "Selfie camera.Single",
    "Selfie camera.Dual",
    "Sound",
    "Battery.Type",
    "Battery.Charging",
    "Comms",
    "Comms.WLAN",
    "Comms.Bluetooth",
    "Comms.USB",
    "Features",
    "Features.Sensors",
    "Misc",
    "Price",
]

SDK_URLS = {
    "windows":
    "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
    "mac":
    "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip",
    "linux":
    "https://dl.google.com/android/repository/platform-tools-latest-linux.zip",
}


def validate_codename(device: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", device))


def format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def fetch_html_with_selenium(url: str, timestamp: int):
    if not SELENIUM_AVAILABLE:
        return None
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    temp_dir = tempfile.mkdtemp(prefix=f"chromedriver_{timestamp}_")
    options.add_argument(f"--user-data-dir={temp_dir}")
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(10)
        driver.get(url)
        return driver.page_source
    except Exception as e:
        logger.error(f"Selenium error: {e}")
        return None
    finally:
        try:
            driver.quit()
        except:
            pass
        shutil.rmtree(temp_dir, ignore_errors=True)


def fetch_html(url: str, use_selenium: bool = False):
    timestamp = int(time.time())
    if use_selenium:
        return fetch_html_with_selenium(url, timestamp)
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Requests error for {url}: {e}")
        return None


def search_gsmarena(query: str, use_selenium: bool = False):
    sanitized_query = re.sub(r"\s+", "+", query.strip())
    normalized_query = re.sub(r"[^a-z0-9]", "_", query.lower().strip())
    for endpoint in SEARCH_ENDPOINTS:
        url = f"{BASE_URL}{endpoint}{sanitized_query}"
        html = fetch_html(url, use_selenium)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for selector in SELECTORS:
            link_tag = soup.select_one(selector)
            if link_tag and link_tag.get("href"):
                href = link_tag["href"].strip()
                full_link = urljoin(BASE_URL + "/", href)
                if re.match(rf"https://www\.gsmarena\.com/.+-\d+\.php$",
                            full_link):
                    return full_link
    fallback_url = f"{BASE_URL}{SEARCH_ENDPOINTS[0]}{sanitized_query}"
    html = fetch_html(fallback_url)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        for link in soup.select('a[href*=".php"]'):
            href = link["href"].lower()
            if re.search(rf"{normalized_query}-\d+\.php", href):
                full_link = urljoin(BASE_URL + "/", href)
                if re.match(r"https://www\.gsmarena\.com/.*-\d+\.php$",
                            full_link):
                    return full_link
    return None


def fetch_device_info(url: str) -> dict:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.select_one(
            'h1[data-spec="modelname"]') or soup.select_one("h1")
        image = (soup.select_one("div.specs-picture img")
                 or soup.select_one("div.specs-photo-main img")
                 or soup.select_one('img[src*=".jpg"]'))
        specs = []
        for table in soup.select("div#specs-list table"):
            category = table.find("th").text.strip() if table.find(
                "th") else ""
            for row in table.select("tr"):
                th, td = row.find("th"), row.find("td", class_="nfo")
                if th and td:
                    label = (f"{category}.{th.text.strip()}"
                             if category not in th.text else th.text.strip())
                    if label in SPEC_CATEGORIES or th.text.strip(
                    ) in SPEC_CATEGORIES:
                        specs.append(
                            f"<b>{th.text.strip()}</b>: {td.text.strip()}")
                if len(specs) >= 16:
                    break
            if len(specs) >= 16:
                break
        return {
            "title": title.text.strip() if title else "Unknown",
            "image": image["src"] if image else None,
            "specs": "\n".join(specs) or "No specifications available",
            "url": url,
        }
    except requests.RequestException as e:
        logger.error(f"Fetch error for {url}: {e}")
        return {
            "title": "Unknown",
            "image": None,
            "specs": "Failed to retrieve data",
            "url": url,
        }


def gsm_command(update: Update, context: CallbackContext):
    message = update.effective_message
    if not context.args:
        message.reply_text("Usage: /gsm <device name>")
        return
    query = " ".join(context.args)
    message.chat.send_action("typing")
    try:
        url = search_gsmarena(query, use_selenium=False)
        if not url and SELENIUM_AVAILABLE:
            url = search_gsmarena(query, use_selenium=True)
        if not url:
            message.reply_text(
                f"No results found for '{query}'. Try something else (e.g., iPhone 16 Pro Max)."
            )
            return
        data = fetch_device_info(url)
        caption = f"<b>{data['title']}</b>\n{data['specs']}"
        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("View full details.", url=data["url"])]])
        if data["image"]:
            try:
                message.reply_photo(
                    photo=data["image"],
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=buttons,
                )
            except Exception as e:
                logger.error(f"Photo send error: {e}")
                message.reply_text(caption,
                                   parse_mode=ParseMode.HTML,
                                   reply_markup=buttons)
        else:
            message.reply_text(caption,
                               parse_mode=ParseMode.HTML,
                               reply_markup=buttons)
    except Exception as e:
        logger.error(f"GSM command error for '{query}': {str(e)}")
        message.reply_text(f"An error occurred while fetching data: {str(e)}")


def get_sdk(update: Update, context: CallbackContext):
    message = update.effective_message
    if not context.args:
        links = [
            f"<b>{escape(name.title())}</b>: <a href='{escape(url)}'>Download</a>"
            for name, url in SDK_URLS.items()
        ]
        message.reply_text(
            "Latest Android SDK Platform Tools:\n" + "\n".join(links),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    os_arg = context.args[0].strip().lower()
    if os_arg in ("macos", "darwin"):
        os_arg = "mac"
    elif os_arg in ("win", ):
        os_arg = "windows"

    if os_arg not in SDK_URLS:
        message.reply_text(
            "<b>Unsupported OS.</b>\n"
            "Please use one of: <b>windows</b>, <b>mac</b>, or <b>linux</b>.",
            parse_mode=ParseMode.HTML,
        )
        return

    url = SDK_URLS[os_arg]
    message.reply_text(
        f"Latest Android SDK Platform Tools for <b>{escape(os_arg.title())}</b>:\n"
        f"<a href='{escape(url)}'>Download</a>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


def kernelsu(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    repos: List[Tuple[str, str]] = [
        ("KernelSU", "tiann/KernelSU"),
        ("KernelSU-Next", "KernelSU-Next/KernelSU-Next"),
    ]
    msg = "*Latest KernelSU Releases*\n\n"

    for repo_name, repo_path in repos:
        try:
            with get(
                    f"https://api.github.com/repos/{repo_path}/releases/latest",
                    headers=HEADERS,
                    timeout=5,
            ) as response:
                response.raise_for_status()
                data = response.json()

                msg += f"*{repo_name}*\n"
                msg += f"• Release: [{data['tag_name']}]({data['html_url']})\n"

                apk_assets = [
                    asset for asset in data["assets"]
                    if asset["name"].lower().endswith(".apk")
                ]
                msg += ("".join(
                    f"• APK: [{asset['name']}]({asset['browser_download_url']})\n"
                    for asset in apk_assets) or "• APK: No APK assets found\n")
                msg += "\n"

        except HTTPError as e:
            msg += f"*{repo_name}*: Failed to fetch release data\n\n"
        except Exception as e:
            logger.error(f"Error fetching {repo_name} release: {str(e)}")
            msg += f"*{repo_name}*: Error fetching data\n\n"

    if "Failed to fetch" in msg or "Error fetching" in msg:
        msg += "_Note: Some data could not be retrieved. Please try again later._"

    message.reply_text(text=msg,
                       parse_mode="MARKDOWN",
                       disable_web_page_preview=True)


def twrp(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    device = " ".join(context.args).strip()

    if not device or not validate_codename(device):
        message.reply_text(
            text=
            "Error: Please provide a valid device codename (e.g., /twrp a3y17lte)",
            parse_mode="MARKDOWN",
        )
        return

    try:
        with get(f"https://eu.dl.twrp.me/{device}", timeout=5) as response:
            if response.status_code == 404:
                message.reply_text(
                    text=f"TWRP is currently unavailable for *{device}*",
                    parse_mode="MARKDOWN",
                )
                return

            page = BeautifulSoup(response.content, "lxml")
            table = page.find("table")
            if not table:
                message.reply_text(
                    text=f"Error: Could not parse TWRP data for *{device}*",
                    parse_mode="MARKDOWN",
                )
                return

            download = table.find("tr").find("a")
            dl_link = f"https://eu.dl.twrp.me{download['href']}"
            dl_file = download.text
            size = page.find("span", {"class": "filesize"}).text
            date = page.find("em").text.strip()

            msg = f"*Latest TWRP Recovery for {device}*\n\n"
            msg += f"• Release Type: `Official`\n"
            msg += f"• Size: `{size}`\n"
            msg += f"• Date: `{date}`\n"
            msg += f"• File: `{dl_file}`\n"

            buttons = [[
                InlineKeyboardButton(text="Download TWRP", url=dl_link)
            ]]

            message.reply_text(
                text=msg,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="MARKDOWN",
                disable_web_page_preview=True,
            )

    except Exception as e:
        logger.error(f"Error in twrp command for {device}: {str(e)}")
        message.reply_text(
            text="An unexpected error occurred. Please try again later.",
            parse_mode="MARKDOWN",
        )


def orangefox(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    device = " ".join(context.args).strip()

    if not device or not validate_codename(device):
        message.reply_text(
            text=
            "Error: Please provide a valid device codename (e.g., /orangefox a3y17lte)",
            parse_mode="MARKDOWN",
        )
        return

    try:
        with get(
                f"https://api.orangefox.download/v3/releases/?codename={device}&sort=date_desc&limit=1",
                timeout=5,
        ) as response:
            if response.status_code == 404 or not response.content:
                send_response(
                    message,
                    f"OrangeFox Recovery is not available for *{device}*",
                    device,
                )
                return

            page = loads(response.content)
            if not page.get("data"):
                send_response(
                    message,
                    f"OrangeFox Recovery is not available for *{device}*",
                    device,
                )
                return

            file_id = page["data"][0]["_id"]

            with get(
                    f"https://api.orangefox.download/v3/devices/get?codename={device}",
                    timeout=5,
            ) as response:
                page = loads(response.content)
                if page.get("detail") == "Not Found":
                    send_response(
                        message,
                        f"OrangeFox Recovery is not available for *{device}*",
                        device,
                    )
                    return

                oem = page.get("oem_name", "Unknown")
                model = page.get("model_name", "Unknown")
                full_name = page.get("full_name", device)
                maintainer = page.get("maintainer",
                                      {}).get("username", "Unknown")

            with get(
                    f"https://api.orangefox.download/v3/releases/get?_id={file_id}",
                    timeout=5,
            ) as response:
                page = loads(response.content)
                dl_file = page.get("filename", "Unknown")
                build_type = page.get("type", "Unknown")
                version = page.get("version", "Unknown")
                changelog = page.get("changelog",
                                     ["No changelog available"])[0]
                size = format_size(page.get("size", 0))
                mirrors = page.get("mirrors", {})
                date = datetime.fromtimestamp(page.get("date",
                                                       0)).strftime("%Y-%m-%d")
                md5 = page.get("md5", "Unknown")

                dl_link = mirrors.get("DL", "")
                if not (dl_link and isinstance(dl_link, str)
                        and dl_link.startswith("http")):
                    dl_link = next(
                        (mirrors[key]
                         for key in mirrors if isinstance(mirrors[key], str)
                         and mirrors[key].startswith("http")),
                        "",
                    )

                msg = f"*Latest OrangeFox Recovery for {full_name}*\n\n"
                msg += f"• Manufacturer: `{oem}`\n"
                msg += f"• Model: `{model}`\n"
                msg += f"• Codename: `{device}`\n"
                msg += f"• Build Type: `{build_type}`\n"
                msg += f"• Maintainer: `{maintainer}`\n"
                msg += f"• Version: `{version}`\n"
                msg += f"• Changelog: `{changelog}`\n"
                msg += f"• Size: `{size}`\n"
                msg += f"• Date: `{date}`\n"
                msg += f"• File: `{dl_file}`\n"
                msg += f"• MD5: `{md5}`\n"

                buttons = [[
                    InlineKeyboardButton(
                        text="Check OrangeFox Website",
                        url=f"https://orangefox.download/device/{device}",
                    )
                ]]
                if dl_link:
                    buttons.insert(
                        0,
                        [
                            InlineKeyboardButton(text="Download OrangeFox",
                                                 url=dl_link)
                        ],
                    )
                else:
                    msg += "\n_Direct download link unavailable. Please check the OrangeFox website for download options._"

                send_response(message, msg, device, buttons)

    except Exception as e:
        logger.error(f"Error in orangefox command for {device}: {str(e)}")
        send_response(message,
                      "An unexpected error occurred. Please try again later.",
                      device)


def send_response(
    message,
    text: str,
    device: str,
    buttons: Optional[List[List[InlineKeyboardButton]]] = None,
) -> None:
    for attempt in range(3):
        try:
            message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons)
                if buttons else None,
                parse_mode="MARKDOWN",
                disable_web_page_preview=True,
            )
            return
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            else:
                logger.error(
                    f"Failed to send message for {device} after 3 attempts: {str(e)}"
                )
                message.reply_text(
                    text="Failed to send response. Please try again later.",
                    parse_mode="MARKDOWN",
                )


__help__ = """
Android device recoveries, kernels, and SDK tools.

• /gsm <device> - Get specs and images of a phone (e.g., /gsm iPhone 16 Pro Max).

• /sdk - Get latest Android SDK Platform Tools for all OS (Windows, Mac, Linux).
• /sdk <os> - Get SDK Platform Tools for a specific OS (e.g., /sdk windows).

• /orangefox <codename> - Fetch latest OrangeFox recovery for a device (e.g., /orangefox a40).
• /twrp <codename> - Fetch latest TWRP recovery for a device (e.g., /twrp a40).

• /kernelsu - Get latest KernelSU releases from GitHub.
"""

__mod_name__ = "Android"

dispatcher.add_handler(CommandHandler("gsm", gsm_command, run_async=True))
dispatcher.add_handler(CommandHandler("sdk", get_sdk, run_async=True))
dispatcher.add_handler(CommandHandler("kernelsu", kernelsu, run_async=True))
dispatcher.add_handler(CommandHandler("twrp", twrp, run_async=True))
dispatcher.add_handler(CommandHandler("orangefox", orangefox, run_async=True))
