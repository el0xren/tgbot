import time
import threading
import logging
import heapq
from datetime import timedelta
from telegram import Update, ParseMode
from telegram.ext import CommandHandler, CallbackContext
from telegram.utils.helpers import mention_html
from tg_bot.modules.sql import timer_sql as sql
from tg_bot.modules.helper_funcs.chat_status import user_admin


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

timer_queue = []
timer_queue_lock = threading.Condition()
timer_events = {}
timer_counter = {}


def format_time_left(seconds: int) -> str:
    return str(timedelta(seconds=seconds))


def parse_duration(s: str) -> int:
    import re
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800,
        'y': 31536000
    }
    total = 0
    for amount, unit in re.findall(r"(\d+)([smhdwy])", s.lower()):
        total += int(amount) * multipliers[unit]
    return total


def notify_expired(chat_id: int, user_id: int, reason: str, context: CallbackContext):
    try:
        user_mention = mention_html(user_id, "Reminder")
        context.bot.send_message(
            chat_id=chat_id,
            text=f"{user_mention}: Your timer{' for ' + reason if reason else ''} has expired.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to notify user {user_id} in chat {chat_id}: {e}")


def timer_manager(context: CallbackContext):
    last_cleanup = 0
    while True:
        with timer_queue_lock:
            if not timer_queue:
                timer_queue_lock.wait()
                continue
            now = int(time.time())
            if now - last_cleanup >= 300:
                sql.clear_expired(now)
                last_cleanup = now
            end_time, chat_id, user_id, reason = timer_queue[0]
            if end_time <= now:
                heapq.heappop(timer_queue)
                key = (chat_id, user_id, end_time)
                timer_exists = sql.get_user_timers(chat_id, user_id)
                timer_exists = any(t.end_time == end_time for t in timer_exists)
                if timer_exists and key in timer_events and not timer_events[key].is_set():
                    notify_expired(chat_id, user_id, reason, context)
                    sql.remove_timer(chat_id, user_id, end_time)
                if key in timer_events:
                    del timer_events[key]
                counter_key = (chat_id, user_id, end_time - (end_time % 1000))
                if counter_key in timer_counter:
                    timer_counter[counter_key] -= 1
                    if timer_counter[counter_key] <= 0:
                        del timer_counter[counter_key]
                continue
            wait_time = end_time - now
            timer_queue_lock.wait(timeout=min(wait_time, 1))


def start_timer(chat_id: int, user_id: int, duration: int, reason: str, context: CallbackContext):
    cancel_event = threading.Event()
    base_end_time = int(time.time()) + duration
    with timer_queue_lock:
        counter_key = (chat_id, user_id, base_end_time)
        timer_counter[counter_key] = timer_counter.get(counter_key, 0) + 1
        end_time = base_end_time + (timer_counter[counter_key] - 1)

    added = sql.add_timer(chat_id, user_id, end_time, reason)
    if not added:
        with timer_queue_lock:
            timer_counter[counter_key] -= 1
            if timer_counter[counter_key] <= 0:
                del timer_counter[counter_key]
        return None

    with timer_queue_lock:
        heapq.heappush(timer_queue, (end_time, chat_id, user_id, reason))
        timer_events[(chat_id, user_id, end_time)] = cancel_event
        timer_queue_lock.notify()
    return cancel_event, end_time


@user_admin
def settimer(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if not args:
        update.message.reply_text("Usage: /settimer <time> [reason]")
        return

    try:
        duration = parse_duration(args[0])
        if duration <= 0:
            raise ValueError("Invalid duration. Example: 1h30m, 45s, 2d5h")
    except Exception:
        update.message.reply_text("Invalid duration. Example: 1h30m, 45s, 2d5h")
        return

    reason = " ".join(args[1:]).strip()
    try:
        result = start_timer(chat.id, user.id, duration, reason, context)
        if result:
            cancel_event, end_time = result
            update.message.reply_text(
                f"Timer set for {format_time_left(duration)}{' with reason: ' + reason if reason else ''}."
            )
    except ValueError as e:
        update.message.reply_text(str(e))


@user_admin
def show_timers(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    now = int(time.time())

    timers = sql.get_user_timers(chat.id, user.id)

    if not timers:
        update.message.reply_text("You have no active timers.")
        return

    lines = ["<b>Active Timers:</b>"]
    active_timers = [t for t in timers if t.end_time > now]
    for i, t in enumerate(active_timers, 1):
        time_left = t.end_time - now
        lines.append(f"{i}. ⏳ {format_time_left(time_left)} — {t.reason or 'No reason'}")
    if not active_timers:
        update.message.reply_text("You have no active timers.")
        return
    lines.append("\nTo cancel a specific timer, use /canceltimer number (e.g., /canceltimer 1)")
    update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


@user_admin
def cancel_timer(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if not args:
        update.message.reply_text("Usage: /canceltimer number (e.g., /canceltimer 1)")
        return

    try:
        index = int(args[0])
        if index < 1:
            raise ValueError
    except ValueError:
        update.message.reply_text("Invalid number. Please provide a number (e.g., /canceltimer 1)")
        return

    timers = sql.get_user_timers(chat.id, user.id)
    active_timers = [t for t in timers if t.end_time > int(time.time())]
    if 0 <= index - 1 < len(active_timers):
        timer = active_timers[index - 1]
        end_time = timer.end_time
        deleted = sql.delete_timer_by_index(chat.id, user.id, index - 1)
        if deleted:
            key = (chat.id, user.id, end_time)
            with timer_queue_lock:
                if key in timer_events:
                    timer_events[key].set()
                    del timer_events[key]
                timer_queue[:] = [(t, c, u, r) for t, c, u, r in timer_queue if (c, u, t) != key]
                heapq.heapify(timer_queue)
                timer_queue_lock.notify()
            counter_key = (chat.id, user.id, end_time - (end_time % 1000))
            if counter_key in timer_counter:
                timer_counter[counter_key] -= 1
                if timer_counter[counter_key] <= 0:
                    del timer_counter[counter_key]
            update.message.reply_text(f"Timer {index} has been canceled.")
        else:
            update.message.reply_text(f"Failed to cancel timer {index}. It may have already expired.")
    else:
        update.message.reply_text(f"No timer found at number {index}. Use /timers to see your active timers.")


@user_admin
def cancel_timers(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user

    timers = sql.get_user_timers(chat.id, user.id)
    with timer_queue_lock:
        for timer in timers:
            key = (chat.id, user.id, timer.end_time)
            if key in timer_events:
                timer_events[key].set()
                del timer_events[key]
            timer_queue[:] = [(t, c, u, r) for t, c, u, r in timer_queue if c != chat.id or u != user.id]
            heapq.heapify(timer_queue)
            counter_key = (chat.id, user.id, timer.end_time - (timer.end_time % 1000))
            if counter_key in timer_counter:
                timer_counter[counter_key] -= 1
                if timer_counter[counter_key] <= 0:
                    del timer_counter[counter_key]
        timer_queue_lock.notify()
    deleted = sql.delete_all_user_timers(chat.id, user.id)
    if deleted:
        update.message.reply_text("All your timers have been canceled.")
    else:
        update.message.reply_text("You have no timers to cancel.")


def rehydrate_timers(dispatcher: CallbackContext):
    now = int(time.time())
    sql.clear_expired(now)
    seen_keys = set()

    for timer in sql.get_all_timers():
        key = (timer.chat_id, timer.user_id, timer.end_time)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        remaining = timer.end_time - now
        if remaining > 0:
            with timer_queue_lock:
                cancel_event = threading.Event()
                heapq.heappush(timer_queue, (timer.end_time, timer.chat_id, timer.user_id, timer.reason))
                timer_events[(timer.chat_id, timer.user_id, timer.end_time)] = cancel_event
                timer_queue_lock.notify()
        else:
            sql.remove_timer(timer.chat_id, timer.user_id, timer.end_time)


__help__ = """
Manage countdown timers that send reminders when they expire.

 - /settimer <duration> <reason>: set a timer that will notify you after the specified duration.
   Example: `/settimer 10m Take a break`
 - /timers: view all active timers you've set.
 - /canceltimer <index>: cancel a specific timer by its index (as shown in /timers).
 - /cancelall: cancel all active timers you've set.

*Supported duration formats:*
 - Seconds: `30s`
 - Minutes: `15m`
 - Hours: `2h`
 - Days: `1d`
You can also combine them, like `1h30m` or `2d3h10m`.

"""

__mod_name__ = "Timers"


def register_timer_handlers(dispatcher):
    threading.Thread(target=timer_manager, args=(dispatcher,), daemon=True).start()
    rehydrate_timers(dispatcher)
    dispatcher.add_handler(CommandHandler("settimer", settimer, run_async=True))
    dispatcher.add_handler(CommandHandler("timers", show_timers, run_async=True))
    dispatcher.add_handler(CommandHandler("canceltimer", cancel_timer, run_async=True))
    dispatcher.add_handler(CommandHandler("cancelall", cancel_timers, run_async=True))

