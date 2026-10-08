"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Lightweight class to hold system-wide context variables

Author: ghoss
License: MIT
===============================================================================
"""

from dataclasses import dataclass
from zoneinfo import ZoneInfo


@dataclass
class RenderContext:

    timezone: ZoneInfo
    canvas_width: int
    canvas_height: int
    
    # Future-proofing: add units, locale, or canvas overrides here
    # units: str = "metric"