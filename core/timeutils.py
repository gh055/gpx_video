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
from datetime import datetime, timezone, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class TimeUtils:

    """
    Get timezone from offset to UTC
    """
    @staticmethod
    def get_timezone(offset):
        return timezone(timedelta(hours=offset))


    """
    Convert datetime string (e.g. "Thu Aug 27 2026 11:06:27") to UNIX epoch in seconds
    """
    @staticmethod
    def dt_to_epoch(dt_string, offset = 0):

        dt = datetime.strptime(dt_string, "%a %b %d %Y %H:%M:%S.%f").replace(tzinfo=timezone.utc)
        return dt.timestamp() + offset


    """
    Calculate timezone adjusted time
    """
    @staticmethod
    def fromtimestamp(t, tz=timezone.utc):

        return datetime.fromtimestamp(t, tz=tz)


    """
    Convert UNIX epoch to datetime string
    """
    @staticmethod
    def epoch_to_dt(epoch):

        return TimeUtils.fromtimestamp(epoch, tz=timezone.utc).strftime("%a %b %d %Y %H:%M:%S")

    
    """
    Create a time object from hours/minutes/seconds
    """
    @staticmethod
    def create_time_obj(hours, minutes, seconds):

        return time(hour=min(hours, 23), minute=minutes, second=seconds)


    """
    Converts SMPTE timecode string (HH:MM:SS:FF or HH:MM:SS;FF) to total
    elapsed wall-clock seconds from midnight.
    """
    @staticmethod
    def tc_to_seconds(tc_string:str, fps=29.97):

        parts = [int(p) for p in re.split(r'[:;]', tc_string)]
        h, m, s = parts[0], parts[1], parts[2]
        f = parts[3] if len(parts) > 3 else 0

        if ';' in tc_string:
            nominal_fps = 30
            drop_frames = 2
            total_minutes = h * 60 + m
            drop_events = total_minutes - (total_minutes // 10)
            total_frames = (h * 3600 + m * 60 + s) * nominal_fps + f - (drop_events * drop_frames)
            return total_frames / (30000 / 1001)
        else:
            nominal_fps = round(fps) if isinstance(fps, float) else fps
            total_frames = (h * 3600 + m * 60 + s) * nominal_fps + f
            return total_frames / nominal_fps


    """
    Combines a clip's start timecode string with a base calendar date string 
    (e.g., '2026-05-08' or GPX start date) to produce an exact UTC Epoch float.
    """
    @staticmethod
    def clip_tc_to_epoch(start_tc, calendar_date_str, tc_offset=0.0, fps=29.97):

        # Convert start TC string to elapsed wall-clock seconds from midnight
        tc_seconds = TimeUtils.tc_to_seconds(start_tc, fps=fps)
        
        # Parse base date (00:00:00 UTC)
        if isinstance(calendar_date_str, str):
            base_dt = datetime.strptime(calendar_date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            date_epoch = base_dt.timestamp()
        else:
            date_epoch = calendar_date_str
            
        # Absolute Start Epoch = Base Date Midnight + Clip Start TC Seconds + User Sync Calibration Offset
        return date_epoch + tc_seconds + tc_offset


    """
    Parses a timezone string into a python tzinfo object.
    Supports IANA names (e.g., 'Europe/Zurich'), 'UTC+X' / 'UTC-X', or numeric offsets.
    """
    @staticmethod
    def parse_timezone(tz_setting):

        if not tz_setting or tz_setting.upper() in ("UTC", "Z"):
            return timezone.utc

        # Handle standard IANA names (e.g., 'Europe/Zurich', 'America/New_York')
        try:
            return ZoneInfo(str(tz_setting))

        except ZoneInfoNotFoundError:
            pass

        # Handle "UTC+X", "UTC-X", "GMT+X", etc.
        utc_match = re.match(r'^(?:UTC|GMT)?([+-]?\d+(?:\.\d+)?)$', str(tz_setting).strip(), re.IGNORECASE)
        if utc_match:
            hours_offset = float(utc_match.group(1))
            return timezone(timedelta(hours=hours_offset))

        # Fallback to UTC if format is unrecognized
        print(f"Warning: Could not parse timezone '{tz_setting}'. Defaulting to UTC.")
        return timezone.utc