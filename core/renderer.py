"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Routines to create individual video frames of the overlay.

Author: ghoss
License: MIT
===============================================================================
"""

import cairo
from cairo import ImageSurface as VideoFrame
from cairo import Context as VideoContext

from core.context import RenderContext
from widgets.factory import WidgetFactory


class OverlayRenderer:

    """
    Initialize rendering engine
    """
    def __init__(self, widgets: dict, render_ctx: RenderContext):

        self.render_ctx = render_ctx

        # Transform dictionary into a list of config dicts with 'name' injected
        widget_configs = [
            {"name": name, **cfg}
            for name, cfg in widgets.items()
            if cfg.get("enabled", True)  # Filter out disabled widgets if needed
        ]

        # Resolve anchors for all enabled widgets in one step
        self.widgets: list[BaseWidget] = WidgetFactory.create_all(widget_configs)     


    """
    Exports a frame to the specified file
    """
    def export(self,
        frame: VideoFrame,
        output_file
        ):

        frame.write_to_png(output_file)
        print(f"Preview written to: {output_file}")


    """
    Creates an empty canvas
    """
    def empty_frame(self) -> tuple[VideoFrame, VideoContext]:

        frame = VideoFrame(
            cairo.FORMAT_ARGB32, 
            self.render_ctx.canvas_width, 
            self.render_ctx.canvas_height
        )
        ctx = cairo.Context(frame)
        return frame, ctx


    """
    Pre-render static track line elements to a reusable surface.
    """
    def draw_template(self, 
        gpx_points,
        dummy_values
        ) -> VideoFrame:
        
        # Create a blank rendering canvas
        self.template, ctx = self.empty_frame()

        # Draw the static portions of all widgets
        for widget in self.widgets:
            widget.draw_template(ctx, gpx_points, dummy_values)

        return self.template


    """
    Render dynamic frame elements on top of static template.
    """
    def draw_frame(self, ctx, frame_time):

        # Initialize background with template
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_surface(self.template, 0, 0)
        ctx.paint()
        ctx.restore()

        # 2. Draw all active widgets sequentially
        for widget in self.widgets:
            widget.draw(ctx, self.render_ctx, frame_time)