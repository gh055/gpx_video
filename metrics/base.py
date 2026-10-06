"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================
- Abstract Base Class for custom telemetry metrics

Author: ghoss
License: MIT
===============================================================================
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


"""
Abstract Base Class that every custom metric calculation must inherit.
"""
class BaseMetric(ABC):

    def __init__(self, config: Dict[str, Any] = None):

        self.config = config or {}


    """
    Indicates whether this metric should automatically register with KalmanFilter1D.
    """
    @property
    def requires_kalman(self) -> bool:

        return False


    """
    Kalman filter parameters if requires_kalman is True.
    """
    @property
    def kalman_config(self) -> Dict[str, float]:

        return {
            'process_variance': 1e-4,
            'measurement_variance': 1.0,
        }


    """
    Calculates the metric for each trackpoint in points.
    Modifies points in-place.
    """
    @abstractmethod
    def calculate(self, points: List[Dict[str, Any]], window: int = 5) -> None:
        
        pass