"""
===============================================================================
Kalman Filtering Engine for Telemetry Data
===============================================================================

- Provides 1D stateful Kalman filtering for scalar telemetry streams (e.g. altitude,
speed, heart rate, cadence). Includes static registry management for smoothing 
configurations across GPX data processing pipelines.

Author: ghoss
License: MIT
===============================================================================
"""

from typing import (
    Dict, List, Optional, Any
)


"""
1D stateful Kalman Filter for scalar telemetry smoothing.
"""
class KalmanFilter1D:

    # Central registry for metrics to be smoothed by default
    _registry: Dict[str, Dict[str, Any]] = {
        'alt': {
            'target_key': 'alt_smoothed',
            'process_variance': 1e-4,
            'measurement_variance': 4.0,  # GPS vertical jitter (~2-4m)
        },
        # 'hr': {
        #     'target_key': 'hr_smoothed',
        #     'process_variance': 1e-2,
        #     'measurement_variance': 1.0,
        # },
        # 'cadence': {
        #     'target_key': 'cadence_smoothed',
        #     'process_variance': 1e-2,
        #     'measurement_variance': 2.0,
        # },
    }


    """
    :param process_variance: How fast the underlying physical process actually changes.
    :param measurement_variance: Sensor noise/error variance.
    :param estimated_error: Initial estimation error covariance.
    """
    def __init__(
        self,
        process_variance: float = 1e-4,
        measurement_variance: float = 1.0,
        estimated_error: float = 1.0
    ):
        self.q = process_variance      # Process noise covariance
        self.r = measurement_variance  # Measurement noise covariance
        self.p = estimated_error       # Estimation error covariance
        self.x: Optional[float] = None # State estimate


    """
    Update filter state with a new measurement and return smoothed estimate.
    """
    def update(self, measurement: Optional[float]) -> Optional[float]:

        if measurement is None:
            return self.x

        if self.x is None:
            self.x = float(measurement)
            return self.x

        # 1. Prediction step
        self.p = self.p + self.q

        # 2. Measurement update (Kalman Gain)
        k = self.p / (self.p + self.r)
        self.x = self.x + k * (measurement - self.x)
        self.p = (1.0 - k) * self.p

        return self.x


    # -------------------------------------------------------------------------
    # Metric Registry Management (Class Methods)
    # -------------------------------------------------------------------------

    """
    Register or update a metric configuration for automatic smoothing.

    :param source_key: Dict key name in trackpoint list (e.g. 'temp', 'speed')
    :param target_key: Dict key where smoothed output will be saved.
                        Defaults to '{source_key}_smoothed'.
    :param process_variance: Filter process noise.
    :param measurement_variance: Filter measurement sensor noise.
    """
    @classmethod
    def register_metric(
        cls,
        source_key: str,
        target_key: Optional[str] = None,
        process_variance: float = 1e-4,
        measurement_variance: float = 1.0
    ) -> None:

        if target_key is None:
            target_key = f"{source_key}_smoothed"

        cls._registry[source_key] = {
            'target_key': target_key,
            'process_variance': process_variance,
            'measurement_variance': measurement_variance
        }


    """
    Remove a metric from the automatic smoothing registry.
    """
    @classmethod
    def unregister_metric(cls, source_key: str) -> None:
        cls._registry.pop(source_key, None)


    """
    Return a copy of the registered metrics dictionary.
    """
    @classmethod
    def get_registered_metrics(cls) -> Dict[str, Dict[str, Any]]:
        return dict(cls._registry)


    # -------------------------------------------------------------------------
    # Pipeline Operations (Class Methods)
    # -------------------------------------------------------------------------

    """
    Pass a sequence of point dicts through 1D Kalman filters for all registered metrics.
    Modifies points in-place and returns the list.
    """
    @classmethod
    def apply_kalman_smoothing(
        cls,
        points: List[Dict[str, Any]],
        decimals: int = 2
    ) -> List[Dict[str, Any]]:

        if not points:
            return points

        # Instantiate dedicated 1D Kalman filter instance per registered metric
        filters = {
            source_key: cls(
                process_variance=cfg['process_variance'],
                measurement_variance=cfg['measurement_variance']
            )
            for source_key, cfg in cls._registry.items()
        }

        # Sequentially stream point data through filters
        for p in points:
            for source_key, cfg in cls._registry.items():
                target_key = cfg['target_key']
                raw_val = p.get(source_key)

                if raw_val is not None:
                    smoothed_val = filters[source_key].update(raw_val)
                    p[target_key] = round(smoothed_val, decimals) if smoothed_val is not None else None
                else:
                    p[target_key] = None

        return points