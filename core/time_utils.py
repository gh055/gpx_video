"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Various timecode and time conversion utilities

Author: ghoss
License: MIT
===============================================================================
"""

import re
from datetime import (
    datetime,
    timezone, 
    time,
    timedelta
)


class TimeUtils:

    """
    Get timezone from offset to UTC
    """
    def get_timezone(offset):
        return timezone(timedelta(hours=offset))


    """
    Convert timecode string (HH:MM:SS:FF or HH:MM:SS;FF) to seconds.
    Supports both Non-Drop Frame (NDF) and Drop Frame (DF) formats.
    """
    def tc_to_seconds(tc_string, offset = 0):

        # Split using either ':' or ';' as delimiters
        parts = [int(p) for p in re.split(r'[:;]', tc_string)]
        h, m, s, f = parts[0], parts[1], parts[2], parts[3]
        
        return (h * 3600 + m * 60 + s) + offset


    """
    Convert datetime string (e.g. "Thu Aug 27 2026 11:06:27") to UNIX epoch in seconds
    """
    def dt_to_epoch(dt_string, offset = 0):

        dt = datetime.strptime(dt_string, "%a %b %d %Y %H:%M:%S").replace(tzinfo=timezone.utc)
        return int(dt.timestamp() + offset)


    """
    Calculate timezone adjusted time
    """
    def fromtimestamp(t, tz=timezone.utc):
        return datetime.fromtimestamp(t, tz=tz)


    """
    Convert UNIX epoch to datetime string
    """
    def epoch_to_dt(epoch):
        return self.fromtimestamp(epoch, tz).strftime("%a %b %d %Y %H:%M:%S")

    
    """
    Create a time object from hours/minutes/seconds
    """
    def create_time_obj(hours, minutes, seconds):
        return time(hour=min(hours, 23), minute=minutes, second=seconds)