"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Custom widget to render a GPX track and current position

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
@WidgetFactory.register("track")


class TrackWidget(BaseWidget):

    def __init__(self, config: dict, widget_registry: dict[str, BaseWidget] = None):

        # Forward both config and widget_registry to BaseWidget
        super().__init__(config, widget_registry=widget_registry)

        track = config.get("track", {})
        self.color = track.get("color", (1.0, 1.0, 1.0, 1.0))  # RGBA
        self.line_width = track.get("line_width", 8)
        self.glow_width = track.get("glow_width", 16)

        marker = config.get("marker", {})
        self.marker_size = marker.get("radius", 16)
        self.marker_color = marker.get("color", (1.0, 0.498, 0.0, 1.0))  # RGBA


    """
    Helper method to normalize GPX points to canvas coordinate system
    """
    def __normalize(self, gpx_points):

        # Extract all lat/lon values for min/max calculation
        lats = [p['lat'] for p in gpx_points]
        lons = [p['lon'] for p in gpx_points]

        # Calculate bounds
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        # Calculate scale factors to fit within long edge size
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon

        # Determine scaling factor based on the larger dimension
        if (lat_range > 0 and lon_range > 0):
            scale_factor = (self.width / max(lat_range, lon_range)) 
        else:
            scale_factor = 1.0

        # Convert coordinates to normalized pixel positions (within bounding box)
        normalized_points = []
        for point in gpx_points:
            if lat_range > 0 and lon_range > 0:
                x = self.x + ((point['lon'] - min_lon) * scale_factor)
                y = self.y + ((max_lat - point['lat']) * scale_factor)
            else:
                x = self.x + self.width * 0.5
                y = self.y + self.width * 0.5

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

        # Get all coordinates in normalized GPX path
        points = self.__normalize(gpx_points)
        self.normalized_points = points

        # Set up interpolator
        timestamps = [p['time'] for p in gpx_points]
        self.interpolator = WidgetDataInterpolator(timestamps, points)
        
        # Reduce spikes
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)

        # 1. Helper function to apply the path to the context
        def apply_path():
            ctx.move_to(points[0][0], points[0][1])
            for x, y in points[1:]:
                ctx.line_to(x, y)

        # 2. Multi-pass dark glow / outer shadow (draw wide to narrow with low alpha)
        glow_passes = [
            (22.0, 0.15),  # Mid glow
            (16.0, 0.25)   # Tight inner shadow
        ]
        glow_passes = []

        apply_path()
        for width, alpha in glow_passes:
            ctx.set_source_rgba(0.0, 0.0, 0.0, alpha)
            ctx.set_line_width(width)
            ctx.stroke_preserve()
        
        # Clear path after glow passes
        ctx.new_path()

        # Main solid black outline
        apply_path()
        ctx.set_source_rgba(0.0, 0.0, 0.0, 0.8)
        ctx.set_line_width(self.glow_width)
        ctx.stroke_preserve()

        # Main inner track line
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