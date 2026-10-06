"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================
- Registration routines and dynamic factory for custom telemetry metrics

Author: ghoss
License: MIT
===============================================================================
"""

import importlib
import pkgutil
from typing import Dict, List, Type

from metrics.base import BaseMetric
import metrics.custom


class MetricFactory:

    _registry: Dict[str, Type[BaseMetric]] = {}
    _discovered: bool = False


    """
    Decorator to register a custom metric class under a given name.
    """
    @classmethod
    def register(cls, name: str):

        def decorator(metric_cls: Type[BaseMetric]):

            cls._registry[name] = metric_cls
            return metric_cls

        return decorator


    """
    Dynamically imports all modules inside the metrics.custom package.
    """
    @classmethod
    def _discover_custom_metrics(cls):

        if cls._discovered:
            return

        package = metrics.custom
        package_path = package.__path__

        for _, module_name, _ in pkgutil.iter_modules(package_path):

            if not module_name.startswith("_"):
                importlib.import_module(f"metrics.custom.{module_name}")

        cls._discovered = True


    """
    Returns all discovered metric classes.
    """
    @classmethod
    def get_registered_metrics(cls) -> Dict[str, Type[BaseMetric]]:

        cls._discover_custom_metrics()
        return dict(cls._registry)


    """
    Instantiates all registered custom metrics.
    If configs is provided, matching metric configurations will be passed to __init__.
    """
    @classmethod
    def create_all(cls, configs: List[dict] = None) -> List[BaseMetric]:

        cls._discover_custom_metrics()

        instances = []
        config_map = {cfg.get('type'): cfg for cfg in (configs or [])}

        for name, metric_cls in cls._registry.items():

            cfg = config_map.get(name, {})
            if cfg.get('enabled', True):
                instances.append(metric_cls(cfg))

        return instances