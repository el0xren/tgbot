import threading
import time
from sqlalchemy import Column, String, Integer, Text
from tg_bot.modules.sql import BASE, SESSION, engine


class Timer(BASE):
    __tablename__ = "timers"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(String(14), primary_key=True)
    end_time = Column(Integer, primary_key=True)
    reason = Column(Text)

    def __init__(self, chat_id, user_id, end_time, reason):
        self.chat_id = str(chat_id)
        self.user_id = str(user_id)
        self.end_time = int(end_time)
        self.reason = reason

Timer.__table__.create(bind=engine, checkfirst=True)

TIMER_LOCK = threading.RLock()


def add_timer(chat_id, user_id, end_time, reason):
    with TIMER_LOCK:
        chat_id = str(chat_id)
        user_id = str(user_id)
        end_time = int(end_time)

        timer_count = SESSION.query(Timer).filter_by(chat_id=chat_id, user_id=user_id).count()
        if timer_count >= 5:
            raise ValueError("You already have 5 active timers in this chat. Please cancel one before creating a new one.")

        existing = SESSION.query(Timer).filter_by(chat_id=chat_id, user_id=user_id, end_time=end_time).first()
        if existing:
            return False

        timer = Timer(chat_id, user_id, end_time, reason)
        SESSION.add(timer)
        SESSION.commit()
        return True


def get_all_timers():
    with TIMER_LOCK:
        timers = SESSION.query(Timer).all()
        return timers


def get_user_timers(chat_id, user_id):
    with TIMER_LOCK:
        timers = SESSION.query(Timer).filter_by(chat_id=str(chat_id), user_id=str(user_id)).order_by(Timer.end_time.asc()).all()
        return timers


def remove_timer(chat_id, user_id, end_time):
    with TIMER_LOCK:
        timer = SESSION.query(Timer).filter_by(
            chat_id=str(chat_id),
            user_id=str(user_id),
            end_time=int(end_time)
        ).first()
        if timer:
            SESSION.delete(timer)
            SESSION.commit()
            return True
        return False


def delete_timer_by_index(chat_id, user_id, index):
    with TIMER_LOCK:
        now = int(time.time())
        timers = [t for t in SESSION.query(Timer).filter_by(chat_id=str(chat_id), user_id=str(user_id)).order_by(Timer.end_time.asc()).all() if t.end_time > now]
        if 0 <= index < len(timers):
            timer = timers[index]
            SESSION.delete(timer)
            SESSION.commit()
            return True
        return False


def delete_all_user_timers(chat_id, user_id):
    with TIMER_LOCK:
        timers = SESSION.query(Timer).filter_by(chat_id=str(chat_id), user_id=str(user_id)).all()
        if not timers:
            return False
        for timer in timers:
            SESSION.delete(timer)
        SESSION.commit()
        return True


def clear_expired(current_time):
    with TIMER_LOCK:
        expired = SESSION.query(Timer).filter(Timer.end_time <= int(current_time)).all()
        if expired:
            for timer in expired:
                SESSION.delete(timer)
            SESSION.commit()
