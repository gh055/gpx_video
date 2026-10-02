"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Custom widget to render a static text element

Author: ghoss
License: MIT
===============================================================================
"""

import cairo

# Decorator for auto-discovery
from widgets.base import BaseWidget
from widgets.factory import WidgetFactory

@WidgetFactory.register("static_text")


class StaticTextWidget(BaseWidget):

    def __init__(self, config: dict, widget_registry: dict[str, BaseWidget] = None):

        # Forward both config and widget_registry to BaseWidget
        super().__init__(config, widget_registry=widget_registry)

        self.text = config.get("text", "")
        self.height = self.height or 24

        self.color = self.style.get("color", (1.0, 1.0, 1.0, 1.0))  # RGBA
        self.font_family = self.style.get("font_family", "Sans")
        self.align = self.style.get("align", "left").lower()
        self.stroke_width = self.style.get("stroke_width", 6)
        self.outline_color = self.style.get("outline_color", [0.0, 0.0, 0.0, 0.8])


    """
    Draw static elements of the widget onto the Cairo context.
    """
    def draw_template(self, 
        ctx: cairo.Context, 
        gpx_points, 
        dummy_values
        ):

        ctx.select_font_face(self.font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(self.height)

        # Measure text path dimensions
        extents = ctx.text_extents(self.text)
        half_stroke = self.stroke_width * 0.5

        # 1. Calculate base text path X origin based on alignment
        if self.align == "right":
            # Subtract text advance AND the right half of the stroke
            draw_x = self.x + self.width - extents.x_advance - extents.x_bearing - half_stroke

        elif self.align == "center":
            draw_x = self.x + (self.width - extents.x_advance - extents.x_bearing) * 0.5

        else:  # "left"
            # Add the left half of the stroke so the left border starts flush at self.x
            draw_x = self.x + half_stroke

        ctx.move_to(draw_x, self.y + self.height)
        ctx.text_path(self.text)

        # Stroke outline
        ctx.set_source_rgba(*self.outline_color)
        ctx.set_line_width(self.stroke_width)

        ctx.stroke_preserve()
        ctx.set_source_rgba(*self.color)
        ctx.fill()


    """
    Draw the widget onto the Cairo ctx using frame_data.
    frame_data contains current point telemetry: x, y, alt, hr, temp, etc.
    """
    def draw(self, ctx: cairo.Context, frame_time):
        
        # Static text already drawn in template
        return