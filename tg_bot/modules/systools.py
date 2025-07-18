import requests
import re
import os
import time
import platform
import socket
import psutil
import datetime
import logging
import urllib.request

from datetime import datetime, timedelta
from subprocess import Popen, PIPE, check_output
from speedtest import Speedtest
from functools import lru_cache
from typing import Dict, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CommandHandler, CallbackContext, Filters
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.error import TelegramError

from tg_bot import dispatcher, CallbackContext, OWNER_ID, DEV_USERS, SUDO_USERS
from tg_bot.modules.sql.systools_sql import last_speedtest
from tg_bot.modules.helper_funcs.chat_status import owner_plus, dev_plus, sudo_plus


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_START_TIME = time.time()
ALLOWED_METRICS = {
    "host", "platform", "boot", "uptime", "python", "git", "pid", "threads",
    "cpu", "temp", "load", "memory", "swap", "disk", "network", "owner", "battery",
    "diskio", "cpu_cores", "core_count", "process_start", "system_uptime",
    "cpu_freq", "packages", "latency"
}
class Cache:
    def __init__(self, ttl: int = 300):
        self.cache = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
        return None

    def set(self, key: str, value: any) -> None:
        self.cache[key] = (value, time.time())

cache = Cache()

class SystemMonitor:
    
    @staticmethod
    @lru_cache(maxsize=1)
    def get_hostname() -> str:
        try:
            return socket.gethostname()
        except Exception as e:
            logger.error(f"Error getting hostname: {e}")
            return "Unknown"

    @staticmethod
    @lru_cache(maxsize=1)
    def get_platform_info() -> str:
        try:
            u = platform.uname()
            return f"{u.system} {u.release} ({u.machine})"
        except Exception as e:
            logger.error(f"Error getting platform info: {e}")
            return "Unknown"

    @staticmethod
    @lru_cache(maxsize=1)
    def get_python_version() -> str:
        try:
            import sys
            return sys.version.split()[0]
        except Exception as e:
            logger.error(f"Error getting Python version: {e}")
            return "Unknown"

    @staticmethod
    @lru_cache(maxsize=1)
    def get_git_commit() -> str:
        try:
            if not os.path.isdir(".git") or not os.path.isfile(".git/HEAD"):
                return "N/A (No valid Git repository)"
            with open(".git/HEAD", "r") as f:
                head_content = f.read().strip()
                if not head_content.startswith("ref:") and not head_content.startswith("commit"):
                    return "N/A (Invalid HEAD)"
            return check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
        except Exception as e:
            logger.error(f"Error getting git commit: {e}")
            return "N/A"

    @staticmethod
    def get_load() -> str:
        try:
            if os.name != "nt":
                return ", ".join(f"{x:.2f}" for x in os.getloadavg())
            return "N/A"
        except Exception as e:
            logger.error(f"Error getting load average: {e}")
            return "N/A"

    @staticmethod
    def get_memory() -> str:
        try:
            mem = psutil.virtual_memory()
            return f"{mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB ({mem.percent}%)"
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return "N/A"

    @staticmethod
    def get_swap() -> str:
        try:
            swap = psutil.swap_memory()
            return f"{swap.used // (1024**2)}MB / {swap.total // (1024**2)}MB ({swap.percent}%)"
        except Exception as e:
            logger.error(f"Error getting swap info: {e}")
            return "N/A"

    @staticmethod
    def get_disk() -> str:
        try:
            disk = psutil.disk_usage('/')
            return f"{disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB ({disk.percent}%)"
        except Exception as e:
            logger.error(f"Error getting disk info: {e}")
            return "N/A"

    @staticmethod
    def get_cpu_usage() -> str:
        try:
            return f"{psutil.cpu_percent(interval=0.1)}%"
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return "N/A"

    @staticmethod
    def get_cpu_temp() -> str:
        try:
            temps = psutil.sensors_temperatures()
            if "coretemp" in temps:
                return f"{temps['coretemp'][0].current:.1f}°C"
            elif "cpu_thermal" in temps:
                return f"{temps['cpu_thermal'][0].current:.1f}°C"
            return "N/A"
        except Exception as e:
            logger.error(f"Error getting CPU temperature: {e}")
            return "N/A"

    @staticmethod
    def get_cpu_cores() -> str:
        try:
            cores = psutil.cpu_percent(percpu=True)
            return ", ".join(f"Core {i}: {usage}%" for i, usage in enumerate(cores))
        except Exception as e:
            logger.error(f"Error getting CPU core usage: {e}")
            return "N/A"

    @staticmethod
    def get_cpu_core_count() -> str:
        try:
            physical = psutil.cpu_count(logical=False)
            logical = psutil.cpu_count(logical=True)
            return f"Physical: {physical}, Logical: {logical}"
        except Exception as e:
            logger.error(f"Error getting CPU core count: {e}")
            return "N/A"

    @staticmethod
    def get_network_io() -> str:
        try:
            net = psutil.net_io_counters()
            return f"Sent: {net.bytes_sent // (1024**2)}MB, Recv: {net.bytes_recv // (1024**2)}MB"
        except Exception as e:
            logger.error(f"Error getting network IO: {e}")
            return "N/A"

    @staticmethod
    def get_disk_io() -> str:
        try:
            io = psutil.disk_io_counters()
            if io:
                return f"Read: {io.read_bytes // (1024**2)}MB, Write: {io.write_bytes // (1024**2)}MB"
            return "N/A"
        except Exception as e:
            logger.error(f"Error getting disk IO: {e}")
            return "N/A"

    @staticmethod
    def get_battery() -> str:
        try:
            battery = psutil.sensors_battery()
            if battery:
                return f"{battery.percent}% (Plugged in: {battery.power_plugged})"
            return "N/A"
        except Exception as e:
            logger.error(f"Error getting battery info: {e}")
            return "N/A"

    @staticmethod
    def get_uptime() -> str:
        try:
            return str(timedelta(seconds=int(time.time() - BOT_START_TIME)))
        except Exception as e:
            logger.error(f"Error getting uptime: {e}")
            return "N/A"

    @staticmethod
    def get_boot_time() -> str:
        try:
            return datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Error getting boot time: {e}")
            return "N/A"

    @staticmethod
    def get_process_info() -> Dict[str, str]:
        try:
            process = psutil.Process(os.getpid())
            mem = process.memory_info()
            return {
                "pid": str(os.getpid()),
                "threads": str(process.num_threads()),
                "rss": f"{mem.rss // (1024**2)}MB",
                "vms": f"{mem.vms // (1024**2)}MB",
                "cpu_percent": f"{process.cpu_percent(interval=0.1)}%"
            }
        except Exception as e:
            logger.error(f"Error getting process info: {e}")
            return {"pid": "N/A", "threads": "N/A", "rss": "N/A", "vms": "N/A", "cpu_percent": "N/A"}

    @staticmethod
    def get_process_start() -> str:
        try:
            process = psutil.Process(os.getpid())
            return datetime.fromtimestamp(process.create_time()).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Error getting process start time: {e}")
            return "N/A"

    @staticmethod
    def get_system_uptime() -> str:
        try:
            boot_time = psutil.boot_time()
            return str(timedelta(seconds=int(time.time() - boot_time)))
        except Exception as e:
            logger.error(f"Error getting system uptime: {e}")
            return "N/A"

    @staticmethod
    def get_cpu_freq() -> str:
        try:
            freq = psutil.cpu_freq()
            if freq:
                return f"Current: {freq.current:.1f}MHz, Max: {freq.max:.1f}MHz"
            return "N/A"
        except Exception as e:
            logger.error(f"Error getting CPU frequency: {e}")
            return "N/A"

    @staticmethod
    def get_package_versions() -> str:
        try:
            import pkg_resources
            packages = ["python-telegram-bot", "psutil"]
            versions = [f"{pkg}: {pkg_resources.get_distribution(pkg).version}" for pkg in packages if pkg_resources.get_distribution(pkg)]
            return ", ".join(versions) if versions else "N/A"
        except Exception as e:
            logger.error(f"Error getting package versions: {e}")
            return "N/A"

    @staticmethod
    def get_network_latency() -> str:
        try:
            if os.name == "nt":
                output = check_output(["ping", "-n", "1", "8.8.8.8"]).decode()
                for line in output.splitlines():
                    if "time=" in line:
                        return line.split("time=")[1].split()[0]
            else:
                output = check_output(["ping", "-c", "1", "8.8.8.8"]).decode()
                for line in output.splitlines():
                    if "time=" in line:
                        return line.split("time=")[1].split()[0] + "ms"
            return "N/A"
        except Exception as e:
            logger.error(f"Error getting network latency: {e}")
            return "N/A"


@dev_plus
def status(update: Update, context: CallbackContext):
    try:
        monitor = SystemMonitor()
        args = context.args
        selected_metrics = set(args) if args else ALLOWED_METRICS

        metrics = {}
        if not args or "host" in selected_metrics:
            metrics["host"] = monitor.get_hostname()
        if not args or "platform" in selected_metrics:
            metrics["platform"] = monitor.get_platform_info()
        if not args or "boot" in selected_metrics:
            metrics["boot"] = monitor.get_boot_time()
        if not args or "uptime" in selected_metrics:
            metrics["uptime"] = monitor.get_uptime()
        if not args or "python" in selected_metrics:
            metrics["python"] = monitor.get_python_version()
        if not args or "git" in selected_metrics:
            metrics["git"] = monitor.get_git_commit()
        if not args or any(metric in selected_metrics for metric in {"pid", "threads", "rss", "vms", "cpu_percent"}):
            metrics.update(monitor.get_process_info())
        if not args or any(metric in selected_metrics for metric in {"cpu", "temp", "cpu_cores", "core_count"}):
            metrics["cpu"] = monitor.get_cpu_usage()
            metrics["temp"] = monitor.get_cpu_temp()
            metrics["cpu_cores"] = monitor.get_cpu_cores()
            metrics["core_count"] = monitor.get_cpu_core_count()
        if not args or "load" in selected_metrics:
            metrics["load"] = monitor.get_load()
        if not args or "memory" in selected_metrics:
            metrics["memory"] = monitor.get_memory()
        if not args or "swap" in selected_metrics:
            metrics["swap"] = monitor.get_swap()
        if not args or "disk" in selected_metrics:
            metrics["disk"] = monitor.get_disk()
        if not args or "diskio" in selected_metrics:
            metrics["diskio"] = monitor.get_disk_io()
        if not args or "network" in selected_metrics:
            metrics["network"] = monitor.get_network_io()
        if not args or "battery" in selected_metrics:
            metrics["battery"] = monitor.get_battery()
        if not args or "owner" in selected_metrics:
            owner_ids = {str(OWNER_ID)} if isinstance(OWNER_ID, (str, int)) else OWNER_ID
            metrics["owner"] = ", ".join(owner_ids)
        if not args or "process_start" in selected_metrics:
            metrics["process_start"] = monitor.get_process_start()
        if not args or "system_uptime" in selected_metrics:
            metrics["system_uptime"] = monitor.get_system_uptime()
        if not args or "cpu_freq" in selected_metrics:
            metrics["cpu_freq"] = monitor.get_cpu_freq()
        if not args or "packages" in selected_metrics:
            metrics["packages"] = monitor.get_package_versions()
        if not args or "latency" in selected_metrics:
            metrics["latency"] = monitor.get_network_latency()

        text = (
            "<b>System Status:</b>\n"
            f"<code>Host        :</code> {metrics.get('host', 'N/A')}\n"
            f"<code>Platform    :</code> {metrics.get('platform', 'N/A')}\n"
            f"<code>Boot Time   :</code> {metrics.get('boot', 'N/A')}\n"
            f"<code>Uptime      :</code> {metrics.get('uptime', 'N/A')}\n"
            f"<code>Python      :</code> {metrics.get('python', 'N/A')}\n"
            f"<code>Git Commit  :</code> {metrics.get('git', 'N/A')}\n"
            f"<code>PID         :</code> {metrics.get('pid', 'N/A')}\n"
            f"<code>Threads     :</code> {metrics.get('threads', 'N/A')}\n"
            f"<code>Proc Memory :</code> RSS: {metrics.get('rss', 'N/A')} | VMS: {metrics.get('vms', 'N/A')}\n"
            f"<code>Proc CPU    :</code> {metrics.get('cpu_percent', 'N/A')}\n"
            f"<code>CPU Usage   :</code> {metrics.get('cpu', 'N/A')} | Temp: {metrics.get('temp', 'N/A')}\n"
            f"<code>CPU Cores   :</code> {metrics.get('cpu_cores', 'N/A')}\n"
            f"<code>Core Count  :</code> {metrics.get('core_count', 'N/A')}\n"
            f"<code>Load Avg    :</code> {metrics.get('load', 'N/A')}\n"
            f"<code>Memory      :</code> {metrics.get('memory', 'N/A')}\n"
            f"<code>Swap        :</code> {metrics.get('swap', 'N/A')}\n"
            f"<code>Disk        :</code> {metrics.get('disk', 'N/A')}\n"
            f"<code>Disk I/O    :</code> {metrics.get('diskio', 'N/A')}\n"
            f"<code>Network IO  :</code> {metrics.get('network', 'N/A')}\n"
            f"<code>Battery     :</code> {metrics.get('battery', 'N/A')}\n"
            f"<code>Bot Owner   :</code> {metrics.get('owner', 'N/A')}\n"
            f"<code>Proc Start  :</code> {metrics.get('process_start', 'N/A')}\n"
            f"<code>Sys Uptime  :</code> {metrics.get('system_uptime', 'N/A')}\n"
            f"<code>CPU Freq    :</code> {metrics.get('cpu_freq', 'N/A')}\n"
            f"<code>Packages    :</code> {metrics.get('packages', 'N/A')}\n"
            f"<code>Net Latency :</code> {metrics.get('latency', 'N/A')}\n"
        )

        update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
        logger.info(f"System status command executed by user {update.effective_user.id} with args: {args}")
    except TelegramError as e:
        logger.error(f"Telegram error while sending status: {e}")
        update.effective_message.reply_text("An error occurred while fetching system status.")
    except Exception as e:
        logger.error(f"Unexpected error in status command: {e}")
        update.effective_message.reply_text("An unexpected error occurred.")


@owner_plus
def shell(update: Update, context: CallbackContext):
    command = update.message.text.split(' ', 1)
    if len(command) == 1:
        update.message.reply_text('No command to execute was given.')
        return
    command = command[1]
    msg = update.message.reply_text(f"~$ {command}")
    out = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = out.communicate()
    
    import html
    output = html.escape(stderr.decode() + stdout.decode())
    
    update.message.bot.edit_message_text(
        f"<b>~$ {command}</b>\n<code>{output}</code>",
        chat_id=update.message.chat_id,
        message_id=msg.message_id,
        parse_mode="HTML")


@dev_plus
def logs(update: Update, context: CallbackContext):
    user = update.effective_user
    with open("log.txt", "rb") as f:
        context.bot.send_document(document=f, filename=f.name, chat_id=user.id)


@dev_plus
def leave(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if args:
        chat_id = str(args[0])
        leave_msg = " ".join(args[1:])
        try:
            context.bot.send_message(chat_id, leave_msg)
            bot.leave_chat(int(chat_id))
            update.effective_message.reply_text("Left chat.")
        except TelegramError:
            update.effective_message.reply_text(
                "Failed to leave chat for some reason.")
    else:
        chat = update.effective_chat
        kb = [[
            InlineKeyboardButton(text="I am sure of this action.",
                                 callback_data="leavechat_cb_({})".format(
                                     chat.id))
        ]]
        update.effective_message.reply_text(
            "I'm going to leave {}, press the button below to confirm".format(
                chat.title),
            reply_markup=InlineKeyboardMarkup(kb))


def leave_cb(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    if callback.from_user.id not in SUDO_USERS:
        callback.answer(text="This isn't for you", show_alert=True)
        return

    match = re.match(r"leavechat_cb_\((.+?)\)", callback.data)
    chat = int(match.group(1))
    bot.leave_chat(chat_id=chat)
    callback.answer(text="Left chat")


@owner_plus
def get_bot_ip(update: Update, context: CallbackContext):
    """ Sends the bot's IP address, so as to be able to ssh in if necessary.
        OWNER ONLY.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


@sudo_plus
def ping(update: Update, context: CallbackContext):
    message = update.effective_message
    user = update.effective_user

    if user.id != OWNER_ID and user.id not in DEV_USERS and user.id not in SUDO_USERS:
        return message.reply_text("Ping Pong... Your opinion is wrong.")

    before = datetime.now()
    message = update.message.reply_text("Pinging..")
    now = datetime.now()
    res = (now - before).microseconds / 1000
    update.message.bot.edit_message_text(
        f"<b>PONG!</b>\nTime taken: <code>{res}ms</code>",
        update.message.chat_id,
        message.message_id,
        parse_mode=ParseMode.HTML)


@dev_plus
def speedtest(update: Update, context: CallbackContext):
    now = datetime.now()
    if last_speedtest.date is not None and (
            now - last_speedtest.date).seconds < 5 * 60:
        update.message.reply_text(
            f"<b>Download:</b> <code>{last_speedtest.download}</code> mbps\n"
            f"<b>Upload:</b> <code>{last_speedtest.upload}</code> mbps\n\n"
            f"Cached results from {last_speedtest.date.strftime('<code>%m/%d/%Y</code>, <code>%H:%M:%S</code>')}",
            parse_mode=ParseMode.HTML)
        return
    message_id = update.message.reply_text(
        "<code>Running speedtest...</code>",
        parse_mode=ParseMode.HTML).message_id
    speedtest = Speedtest()
    speedtest.get_best_server()
    speedtest.download()
    speedtest.upload()
    speedtest.results.share()
    results_dict = speedtest.results.dict()
    download = str(results_dict["download"] // 10**6)
    upload = str(results_dict["upload"] // 10**6)
    last_speedtest.set_data(now, download, upload)
    context.bot.edit_message_text(
        chat_id=update.message.chat_id,
        message_id=message_id,
        text=f"<b>Download:</b> <code>{download}</code> mbps\n"
        f"<b>Upload:</b> <code>{upload}</code> mbps",
        parse_mode=ParseMode.HTML)


STATUS_HANDLER = CommandHandler("status", status, run_async=True)
SHELL_HANDLER = CommandHandler(["sh", "shell"], shell, run_async=True)
LOG_HANDLER = CommandHandler("logs", logs, run_async=True)
LEAVE_HANDLER = CommandHandler("leave", leave, run_async=True)
LEAVE_CALLBACK = CallbackQueryHandler(leave_cb,
                                      pattern=r"leavechat_cb_",
                                      run_async=True)
IP_HANDLER = CommandHandler("ip", get_bot_ip, run_async=True)
PING_HANDLER = CommandHandler("ping", ping, run_async=True)
SPEEDTEST_HANDLER = CommandHandler("speedtest", speedtest, run_async=True)

dispatcher.add_handler(STATUS_HANDLER)
dispatcher.add_handler(SHELL_HANDLER)
dispatcher.add_handler(LOG_HANDLER)
dispatcher.add_handler(LEAVE_HANDLER)
dispatcher.add_handler(LEAVE_CALLBACK)
dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(SPEEDTEST_HANDLER)
