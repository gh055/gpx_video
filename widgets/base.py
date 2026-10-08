"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Base class for all custom widgets

Author: ghoss
License: MIT
===============================================================================
"""

from abc import ABC, abstractmethod
import cairo

from core.context import RenderContext


class BaseWidget(ABC):

    def __init__(self, config: dict, widget_registry: dict[str, 'BaseWidget'] = None):

        self.name = config.get("name", None)
        self.enabled = config.get("enabled", True)
        self.style = config.get("style", {})

        # Raw coordinates from configuration
        self.x, self.y = config.get("position", (0, 0))

        # Dimensions (optional depending on widget type)
        self.width = config.get("width", 0)
        self.height = config.get("height", 0)

        # Resolve offset to optional anchor widget
        anchor_name = config.get("anchor", None)
        if anchor_name and widget_registry and anchor_name in widget_registry:
            parent_widget = widget_registry[anchor_name]
            self.x += parent_widget.x
            self.y += parent_widget.y


    """
    Draw static elements of the widget onto the Cairo context.
    """
    @abstractmethod
    def draw_template(self, 
        ctx: cairo.Context, 
        gpx_points, 
        dummy_values
        ):

        pass


    """
    Draw the widget onto the Cairo context using frame_data.
    frame_data contains current point telemetry: x, y, alt, hr, temp, etc.
    """
    @abstractmethod
    def draw(self, 
        ctx: cairo.Context, 
        render_ctx: RenderContext, 
        frame_data: dict
        ):

        pass