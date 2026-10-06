"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Gradient calculation metric implementation.

Author: ghoss
License: MIT
===============================================================================
"""

from metrics.base import BaseMetric
from metrics.factory import MetricFactory

@MetricFactory.register("gradient")

class GradientMetric(BaseMetric):

    _key = 'gradient'

    def calculate(self, points: list[dict], window: int = 5) -> None:
        
        n = len(points)
        if n == 0:
            return

        for i in range(n):
            start_idx = max(0, i - window)
            end_idx = min(n - 1, i + window)

            # Sum step_dist values across the window
            delta_dist = sum(points[j]['step_dist'] for j in range(start_idx + 1, end_idx + 1))

            p_start = points[start_idx]
            p_end = points[end_idx]

            # Use alt_smoothed if present, falling back to raw alt
            alt_start = p_start.get('alt_smoothed') if p_start.get('alt_smoothed') is not None else p_start['alt']
            alt_end = p_end.get('alt_smoothed') if p_end.get('alt_smoothed') is not None else p_end['alt']
            delta_alt = alt_end - alt_start

            if delta_dist > 0.5:
                gradient = (delta_alt / delta_dist) * 100.0
            else:
                gradient = 0.0

            points[i][self._key] = round(gradient, 1)