"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Registration routines for custom widgets

Author: ghoss
License: MIT
===============================================================================
"""

import importlib
import pkgutil
from pathlib import Path
from widgets.base import BaseWidget

import widgets.custom


import importlib
import pkgutil
from pathlib import Path
from widgets.base import BaseWidget

import widgets.custom


class WidgetFactory:

    _registry: dict[str, type[BaseWidget]] = {}
    _discovered: bool = False

    """
    Decorator to register a widget class under a given type name.
    """
    @classmethod
    def register(cls, type_name: str):

        def decorator(widget_cls: type[BaseWidget]):
            cls._registry[type_name] = widget_cls
            return widget_cls
        return decorator


    """
    Dynamically imports all modules inside the widgets.custom package.
    """
    @classmethod
    def _discover_custom_widgets(cls):

        if cls._discovered:
            return

        package = widgets.custom
        package_path = package.__path__

        # Iterate over all python modules in widgets/custom/
        for _, module_name, _ in pkgutil.iter_modules(package_path):
            if not module_name.startswith("_"):
                importlib.import_module(f"widgets.custom.{module_name}")

        cls._discovered = True


    """
    Single widget instance creation with anchor lookup context
    """
    @classmethod
    def create(cls, widget_config: dict, widget_registry: dict[str, BaseWidget] = None) -> BaseWidget:
        
        # Auto-discover before attempting to instantiate
        cls._discover_custom_widgets()

        w_type = widget_config.get("type")
        widget_cls = cls._registry.get(w_type)

        if not widget_cls:
            raise ValueError(
                f"Unknown widget type: '{w_type}'. "
                f"Available types: {list(cls._registry.keys())}"
            )
            
        return widget_cls(widget_config, widget_registry=widget_registry)


    """
    Sequentially creates and anchors all enabled widgets from a configuration list.
    """
    @classmethod
    def create_all(cls, widget_configs: list[dict]) -> list[BaseWidget]:

        created_named_widgets: dict[str, BaseWidget] = {}
        widget_instances: list[BaseWidget] = []

        for w_cfg in widget_configs:
            
            if not w_cfg.get("enabled", True):
                continue

            # Pass previously instantiated widgets so the new instance can resolve anchors
            widget = cls.create(w_cfg, widget_registry=created_named_widgets)
            widget_instances.append(widget)

            # Store in registry for downstream relative anchoring if a name exists
            if widget.name:
                created_named_widgets[widget.name] = widget

        return widget_instances