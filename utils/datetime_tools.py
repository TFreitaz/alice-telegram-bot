import pytz
import dateutil

from datetime import datetime, timedelta

utc_tz = pytz.timezone("UTC")
local_tz = pytz.timezone("Brazil/East")


def fromisoformat(isodatetime):
    return dateutil.parser.parse(isodatetime)


def local2utc(dt: datetime):
    utc_dt = dt.replace(tzinfo=local_tz).astimezone(utc_tz)
    return utc_tz.normalize(utc_dt - timedelta(minutes=6))


def utc2local(dt: datetime, normalize=False):
    local_dt = dt.replace(tzinfo=utc_tz).astimezone(local_tz)
    if normalize:
        return local_tz.normalize(local_dt + timedelta(minutes=6))
    return local_dt
