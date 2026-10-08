"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Camera timecode drift compensation vs. GPX track time

Author: ghoss
License: MIT
===============================================================================
"""

import re
from datetime import datetime, timezone

from core.timeutils import TimeUtils


class TimecodeDriftCalculator:

    """
    :param tc_cfg: Dictionary/Section from config file under [timecode]
    :param gpx_start_date: Base date string 'YYYY-MM-DD' from the GPX file
    """
    def __init__(self, tc_cfg, gpx_start_date):

        self.manual_offset = tc_cfg.get("tc_offset")

        # Check if manual offset override is specified
        if self.manual_offset is not None:
            self.scale = 1.0
            self.base_offset = float(self.manual_offset)
            self.auto_drift = False

        else:
            self.auto_drift = True

            # Parse reference points
            first_tc = tc_cfg.get("first_tc")
            first_gpx = tc_cfg.get("first_gpx")
            second_tc = tc_cfg.get("second_tc")
            second_gpx = tc_cfg.get("second_gpx")

            fps = tc_cfg.get("fps", 29.97)
            self.local_tz = TimeUtils.parse_timezone(tc_cfg.get("timezone", "UTC"))

            # Convert timecodes to elapsed seconds from midnight
            t_tc1 = TimeUtils.tc_to_seconds(first_tc, fps)
            t_tc2 = TimeUtils.tc_to_seconds(second_tc, fps)

            # Convert GPX local times to UTC Epoch seconds
            t_gpx1 = self._parse_local_time_to_utc_epoch(first_gpx, gpx_start_date)
            t_gpx2 = self._parse_local_time_to_utc_epoch(second_gpx, gpx_start_date)

            # Calculate scale factor (drift rate) and base offset
            delta_tc = t_tc2 - t_tc1
            delta_gpx = t_gpx2 - t_gpx1

            if delta_tc == 0:
                raise ValueError("first_tc and second_tc cannot be identical.")

            self.scale = delta_gpx / delta_tc
            self.base_offset = t_gpx1 - (self.scale * t_tc1)


    """
    Parses a local GPX time string (e.g. '08:03:25') using the configured
    timezone and converts it to a exact UTC epoch float.
    """
    def _parse_local_time_to_utc_epoch(self, local_time_str, date_str):

        parts = [int(p) for p in local_time_str.split(':')]
        h, m, s = parts[0], parts[1], parts[2]

        # Construct naive datetime object
        naive_dt = datetime.strptime(f"{date_str} {h:02d}:{m:02d}:{s:02d}", "%Y-%m-%d %H:%M:%S")
        
        # Attach the configured timezone (e.g., UTC+2 or Europe/Zurich)
        localized_dt = naive_dt.replace(tzinfo=self.local_tz)
        
        # .timestamp() returns the exact UTC epoch seconds
        return localized_dt.timestamp()


    """
    Calculates the exact drift-compensated UTC Epoch timestamp for any frame.
    """
    def clip_tc_to_true_gpx_epoch(self, start_tc, frame_idx=0, fps=29.97):
        exact_fps = 30000 / 1001 if round(fps, 2) in (29.97, 29.0) else fps
        
        # Calculate raw camera timecode seconds for this specific frame
        raw_frame_tc_sec = start_tc + (frame_idx / exact_fps)

        # Apply drift scaling and base offset
        return (raw_frame_tc_sec * self.scale) + self.base_offset