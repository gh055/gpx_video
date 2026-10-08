"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Custom widget to render a dynamic telemetry text element

Author: ghoss
License: MIT
===============================================================================
"""

import cairo

from widgets.base import BaseWidget
from widgets.factory import WidgetFactory
from widgets.interpolate import WidgetDataInterpolator

from core.context import RenderContext
from core.expressions import SafeExpression
from core.timeutils import TimeUtils

# Decorator for auto-discovery
@WidgetFactory.register("telemetry_text")


class TelemetryTextWidget(BaseWidget):

    def __init__(self, config: dict, widget_registry: dict[str, BaseWidget] = None):

        # Forward both config and widget_registry to BaseWidget
        super().__init__(config, widget_registry=widget_registry)
        
        self.data_key = config.get("data_key", "")
        self.template = config.get("template", "{val}")
        self.formula = config.get("formula", None)  # Optional math formula string

        self.height = self.height or 24

        self.font_family = self.style.get("font_family", "Sans")
        self.color = self.style.get("color", (1.0, 1.0, 1.0, 1.0))  # RGBA
        self.align = self.style.get("align", "left").lower()
        self.stroke_width = self.style.get("stroke_width", 6)
        self.outline_color = self.style.get("outline_color", [0.0, 0.0, 0.0, 0.8])


    """
    Draw static elements of the widget onto the Cairo context.
    """
    def draw_template(self, 
        ctx: cairo.Context, 
        render_ctx: RenderContext,
        gpx_points, 
        dummy_values
        ):

        # Set up interpolator
        timestamps = [p['time'] for p in gpx_points]
        data_points = [p[self.data_key] for p in gpx_points]
        self.interpolator = WidgetDataInterpolator(timestamps, data_points)

        # Draw optional dummy values on static template
        if dummy_values:
            self.draw(ctx, render_ctx, 0) # Dummy frametime (resolves to first timestamp)
            return


    """
    Draw the widget onto the Cairo context using frame_data.
    frame_data contains current point telemetry: x, y, alt, hr, temp, etc.
    """
    def draw(self, 
        ctx: cairo.Context, 
        render_ctx: RenderContext, 
        frame_time
        ):
        
        # Get interpolated key value
        val = self.interpolator.get_value(frame_time)

        if val is None:

            # Safeguard in case of missing values
            text = ""

        elif isinstance(val, (int, float)) and "time" in self.data_key:

            if self.data_key == "elapsed_time":
                # Convert total elapsed seconds into HH:MM:SS components
                total_seconds = int(val)
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                # Create a time object (caps at 23:59:59)
                t_obj = TimeUtils.create_time_obj(hours, minutes, seconds)
                text = self.template.format(val=t_obj)
            else:
                # Absolute epoch GPS timestamp
                dt = TimeUtils.fromtimestamp(val, tz=render_ctx.timezone)
                text = self.template.format(val=dt)

        else:
            
            if self.formula:
                # Evaluate optional formula for non-time values
                display_val = SafeExpression.evaluate(self.formula, {"val": val})
            else:
                display_val = val
            text = self.template.format(val=display_val)

        ctx.select_font_face(self.font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(self.height)

        # Measure text path dimensions
        extents = ctx.text_extents(text)
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
        ctx.text_path(text)
        ctx.set_source_rgba(*self.outline_color)
        ctx.set_line_width(6.0)
        ctx.stroke_preserve()
        ctx.set_source_rgba(*self.color)
        ctx.fill()