import pytz

from datetime import datetime, timedelta

utc_tz = pytz.timezone("UTC")
local_tz = pytz.timezone("Brazil/East")


def local2utc(dt: datetime):
    utc_dt = dt.replace(tzinfo=local_tz).astimezone(utc_tz)
    return utc_tz.normalize(utc_dt - timedelta(minutes=6))


def utc2local(dt: datetime):
    local_dt = dt.replace(tzinfo=utc_tz).astimezone(local_tz)
    # return local_tz.normalize(local_dt + timedelta(minutes=6))
    return local_dt
