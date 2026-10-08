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
import numpy as np
from datetime import datetime

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
            self.base_offset = float(self.manual_offset)
            self.auto_drift = False

        else:
            self.auto_drift = True
            fix_points = tc_cfg.get("fix_points", [])

            if len(fix_points) < 2:
                raise ValueError("At least 2 fix_points are required for drift compensation.")

            self.fps = tc_cfg.get("fps", 29.97)
            self.local_tz = TimeUtils.parse_timezone(tc_cfg.get("timezone", "UTC"))

            gpx_epoch_list = []
            tc_seconds_list = []

            # Parse and gather all calibration points by gpx timestamp and clip timecode
            for pt in fix_points:

                t_gpx = self._parse_local_time_to_utc_epoch(pt["gpx"], gpx_start_date)
                t_tc = TimeUtils.tc_to_seconds(pt["tc"], fps=self.fps)
                
                gpx_epoch_list.append(t_gpx)
                tc_seconds_list.append(t_tc)

            # Sort calibration points by camera TC seconds
            sorted_pairs = sorted(zip(tc_seconds_list, gpx_epoch_list), key=lambda x: x[0])
            self.tc_points = np.array([p[0] for p in sorted_pairs])
            self.gpx_points = np.array([p[1] for p in sorted_pairs])


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
    def clip_tc_to_true_gpx_epoch(self, start_tc, frame_idx=0):

        raw_frame_sec = start_tc + (frame_idx / self.fps)

        if not self.auto_drift:
            # Fallback if manual static offset is used
            return raw_frame_sec + self.base_offset

        else:
            # Piecewise linear interpolation (extrapolates linearly outside bounds)
            return float(np.interp(
                x=raw_frame_sec, 
                xp=self.tc_points, 
                fp=self.gpx_points,
                left=None, # Automatically projects slope linearly outside first/last bounds if needed
                right=None
            ))