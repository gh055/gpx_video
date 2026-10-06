"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Interpolate GPX position and data fields at any given frame time.

Author: ghoss
License: MIT
===============================================================================
"""
    

class WidgetDataInterpolator:

    """
    :param timestamps: List/Array of float timestamps (e.g. UTC epoch)
    :param values: List/Array of corresponding values (floats, ints, or tuples/lists)
    """
    def __init__(self, timestamps, values):

            if len(timestamps) != len(values):
                raise ValueError("Timestamps and values must have the same length.")

            self.timestamps = timestamps
            self.values = values
            self.num_points = len(timestamps)
            self.last_index = 0


    def get_value(self, frame_time):

        n = self.num_points
        
        if n == 0:
            return 0

        if n == 1 or frame_time <= self.timestamps[0]:
            return self.values[0] if self.values[0] is not None else 0

        if frame_time >= self.timestamps[-1]:
            return self.values[-1] if self.values[-1] is not None else 0

        # Stateful O(1) pointer tracking
        idx = self.last_index
        while idx < n - 1 and self.timestamps[idx + 1] < frame_time:
            idx += 1
        while idx > 0 and self.timestamps[idx] > frame_time:
            idx -= 1

        self.last_index = idx

        t_prev = self.timestamps[idx]
        t_next = self.timestamps[idx + 1]
        v_prev = self.values[idx]
        v_next = self.values[idx + 1]

        time_diff = t_next - t_prev
        if time_diff <= 0:
            return v_prev if v_prev is not None else 0

        ratio = (frame_time - t_prev) / time_diff

        # 1. Handle Tuple/List (2D or nD coordinates, e.g., (x, y))
        if isinstance(v_prev, (tuple, list)) and isinstance(v_next, (tuple, list)):
            return tuple(
                p + (n_val - p) * ratio
                for p, n_val in zip(v_prev, v_next)
            )

        # 2. Handle Dicts (e.g., {'x': 10, 'y': 20})
        elif isinstance(v_prev, dict) and isinstance(v_next, dict):
            return {
                k: v_prev[k] + (v_next.get(k, v_prev[k]) - v_prev[k]) * ratio
                for k in v_prev
            }

        # 3. Handle Numeric Scalars (int, float)
        if isinstance(v_prev, (int, float)) and isinstance(v_next, (int, float)):
            return v_prev + (v_next - v_prev) * ratio

        # Safe fallback if one or both boundary values are None
        return v_prev if v_prev is not None else (v_next if v_next is not None else 0.0)