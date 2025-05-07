import threading
from typing import Union
from sqlalchemy import Column, String, Boolean
from tg_bot.modules.sql import SESSION, BASE, engine


class LinkShorteningSettings(BASE):
    __tablename__ = "link_shortening_settings"
    chat_id = Column(String(14), primary_key=True)
    enabled = Column(Boolean, default=False)

    def __init__(self, chat_id: Union[int, str]):
        self.chat_id = str(chat_id)

    def __repr__(self):
        return (
            f"<LinkShorteningSettings(chat_id={self.chat_id}, enabled={self.enabled})>"
        )


LinkShorteningSettings.__table__.create(bind=engine, checkfirst=True)

LINK_SHORTEN_LOCK = threading.RLock()


def is_shortening_enabled(chat_id: Union[int, str]) -> bool:
    chat_id = str(chat_id)
    with LINK_SHORTEN_LOCK:
        setting = SESSION.query(LinkShorteningSettings).get(chat_id)
        return setting.enabled if setting else False


def set_shortening_enabled(chat_id: Union[int, str], enabled: bool):
    chat_id = str(chat_id)
    with LINK_SHORTEN_LOCK:
        setting = SESSION.query(LinkShorteningSettings).get(chat_id)
        if not setting:
            setting = LinkShorteningSettings(chat_id)

        setting.enabled = enabled
        SESSION.add(setting)
        SESSION.commit()
