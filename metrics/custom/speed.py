"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Speed calculation metric implementation.

Author: ghoss
License: MIT
===============================================================================
"""

from metrics.base import BaseMetric
from metrics.factory import MetricFactory

@MetricFactory.register("speed")

class SpeedMetric(BaseMetric):

    _key = 'speed'
    
    def calculate(self, points: list[dict], window: int = 5) -> None:

        n = len(points)
        if n == 0:
            return

        for i in range(n):
            start_idx = max(0, i - window)
            end_idx = min(n - 1, i + window)

            # Sum step_dist values across the window
            delta_dist = sum(points[j]['step_dist'] for j in range(start_idx + 1, end_idx + 1))
            delta_time = points[end_idx]['time'] - points[start_idx]['time']

            if delta_time > 0:
                speed_kmh = (delta_dist / delta_time) * 3.6
            else:
                speed_kmh = 0.0

            points[i][self._key] = round(max(0.0, speed_kmh), 1)