from datetime import datetime
from zoneinfo import ZoneInfo


def current_time_ist():
    return datetime.now(ZoneInfo("Asia/Kolkata"))


