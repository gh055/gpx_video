"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Custom widget to render an elevation profile

Author: ghoss
License: MIT
===============================================================================
"""

import math
import cairo

from core.context import RenderContext

from widgets.base import BaseWidget
from widgets.factory import WidgetFactory
from widgets.interpolate import WidgetDataInterpolator

# Decorator for auto-discovery
@WidgetFactory.register("elev_profile")


class ElevationProfileWidget(BaseWidget):

    def __init__(self, config: dict, widget_registry: dict[str, BaseWidget] = None):

        # Forward both config and widget_registry to BaseWidget
        super().__init__(config, widget_registry=widget_registry)

        profile = config.get("profile", {})
        self.color = profile.get("color", (1.0, 1.0, 1.0, 1.0))  # RGBA
        self.bg_color = profile.get("bg_color", (0.2, 0.2, 0.2, 0.4))  # RGBA
        self.line_width = profile.get("line_width", 8)
        self.glow_width = profile.get("glow_width", 16)

        marker = config.get("marker", {})
        self.marker_size = marker.get("radius", 16)
        self.marker_color = marker.get("color", (1.0, 0.498, 0.0, 1.0))  # RGBA


    """
    Helper method to normalize GPX points to canvas coordinate system
    """
    def __normalize(self, gpx_points):

       # Extract all altitude and distance values for min/max calculation
        alts = [p['alt'] for p in gpx_points]
        dists = [p['distance'] for p in gpx_points]

        # Calculate bounds
        min_alt, max_alt = min(alts), max(alts)
        max_dist = dists[-1] if dists else 0.0

        # Calculate scale factors to fit within long edge size
        alt_range = max_alt - min_alt if max_alt != min_alt else 1.0
        dist_range = max_dist if max_dist > 0 else 1.0

        # Calculate coordinates for the elevation graph profile canvas
        normalized_points = []
        for point in gpx_points:

            # Calculate coordinates for the elevation graph profile canvas
            x = self.x + ((point['distance'] / dist_range) * self.width)
            y = self.y + self.height - (((point['alt'] - min_alt) / alt_range) * self.height)

            normalized_points.append((x, y))

        return normalized_points


    """
    Draw static elements of the widget onto the Cairo context.
    """
    def draw_template(self, 
        ctx: cairo.Context, 
        gpx_points, 
        dummy_values
        ):

        # Get all elevations in normalized GPX path
        points = self.__normalize(gpx_points)
        self.normalized_points = points

        # Set up interpolator
        timestamps = [p['time'] for p in gpx_points]
        self.interpolator = WidgetDataInterpolator(timestamps, points)
        
        # Reduce spikes
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)

        # Semi-transparent filled elevation area
        ctx.move_to(points[0][0], self.y + self.height)

        for x, y in points:
            ctx.line_to(x, y)

        ctx.line_to(points[-1][0], self.y + self.height)
        ctx.close_path()
        ctx.set_source_rgba(*self.bg_color)
        ctx.fill()

        # Outline profile curve line
        ctx.move_to(points[0][0], points[0][1])

        for x, y in points[1:]:
            ctx.line_to(x, y)

        ctx.set_source_rgba(0.0, 0.0, 0.0, 0.8)
        ctx.set_line_width(self.glow_width)
        ctx.stroke_preserve()

        ctx.set_source_rgba(*self.color)
        ctx.set_line_width(self.line_width)
        ctx.stroke()

        # Draw optional dummy marker on static template
        if dummy_values:
            self.draw(ctx, 0) # Dummy frametime (resolves to first timestamp)
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

        # Get interpolated canvas coordinates
        x, y = self.interpolator.get_value(frame_time)

        ctx.set_source_rgba(*self.marker_color)
        ctx.arc(x, y, self.marker_size, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.set_line_width(2.0)
        ctx.arc(x, y, self.marker_size, 0, 2 * math.pi)
        ctx.stroke()