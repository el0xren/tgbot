from datetime import datetime
from threading import Lock


class SpeedtestResult:

    def __init__(self):
        self.date: datetime = None
        self.download: str = None
        self.upload: str = None
        self.lock = Lock()

    def set_data(self, date, download, upload):
        with self.lock:
            self.date: datetime = date
            self.download: str = download
            self.upload: str = upload


last_speedtest = SpeedtestResult()
