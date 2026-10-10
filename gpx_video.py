#!/usr/bin/env python3

"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

A high-performance Python utility for automating the creation and seamless
synchronization of vector-rendered GPX motion graphics overlays directly within
DaVinci Resolve timelines.

Key Features:
-------------
- Apple ProRes 4444 rendering with alpha channel (PyCairo vector drawing).
- Converts video file timecodes to UTC Epoch timestamps for frame-accurate 
  GPX track interpolation.
- Native DaVinci Resolve Integration: Leverages the Resolve Scripting API to
  query timeline and clip metadata.
- Multi-Pass Vector Styling: PyCairo-based track maps with dynamic outer glow
  effects, elevation profiles, and customizable telemetry elements.
- JSON configuration file support for commonly used settings.

Usage:
------
    $ python gpx_video.py --help

Requirements:
-------------
    - Python 3.8+
    - DaVinci Resolve Studio (Scripting API enabled)
    - FFmpeg
    - PyCairo, NumPy, gpxpy

Author: ghoss
License: MIT
===============================================================================
"""

import sys

from core.timeutils import TimeUtils
from core.timecode import TimecodeDriftCalculator
from core.davinci_api import DaVinciResolveSession
from core.arg_parser import parse_arguments
from core.gpx_parser import GPXParser
from core.context import RenderContext
from core.renderer import OverlayRenderer
from core.ffmpeg import FFmpeg


"""
Main execution
"""
if __name__ == "__main__":

    # Parse command line arguments and config file
    args, config = parse_arguments()

    # Get current Davinci Resolve project details
    dr = DaVinciResolveSession()

    # Get the project's video properties
    pr_canvas_width, pr_canvas_height, pr_frame_rate = dr.get_video_props()

    # Override video properties by config values if specified
    cfg_canvas = config.get("canvas", {})
    canvas_width = cfg_canvas.get("width", pr_canvas_width)
    canvas_height = cfg_canvas.get("height", pr_canvas_height)
    frame_rate = cfg_canvas.get("frame_rate", pr_frame_rate)

    # Update config with actual canvas properties
    config['canvas'] = {
        'width': canvas_width,
        'height': canvas_height,
        'frame_rate': frame_rate
    }
    print(f"Using {canvas_width}x{canvas_height} canvas @ {frame_rate} fps.")

    # Read GPX file
    gpx = GPXParser(config.get('gpx', {}))
    gpx_points = gpx.parse()
    print(f"GPX file contains {len(gpx_points)} data points.")

    # Get local timezone
    tc_cfg = config.get("timecode", {})
    local_tz = TimeUtils.parse_timezone(tc_cfg.get("timezone", "UTC"))

    # Extract track base date from GPX file
    gpx_start_epoch = gpx_points[0]['time']
    gpx_start_date = TimeUtils.fromtimestamp(gpx_start_epoch, tz=local_tz).strftime("%Y-%m-%d")

    # Initialize calculator with gpx and timecode configs
    drift_calc = TimecodeDriftCalculator(
        tc_cfg=tc_cfg,
        gpx_start_date=gpx_start_date
    )   

    # Initialize rendering engine
    render_ctx = RenderContext(
        timezone=local_tz,
        canvas_width=canvas_width,
        canvas_height=canvas_height
    )
    renderer = OverlayRenderer(config.get("widgets", {}), render_ctx)

    # Create preview .PNG and exit if output path points to an image file
    output_cfg = config.get('output', {})
    output_path = output_cfg['path']
    if output_path.lower().endswith(".png"):
        # Create a template with dummy values
        static_canvas = renderer.draw_template(gpx_points, True)
        renderer.export(static_canvas, output_path)
        sys.exit(0)

    else:
        # Create a template without dummy values for video generation
        static_canvas = renderer.draw_template(gpx_points, False)  
        output_prefix = output_cfg.get('prefix', 'gpx')

    # Extract clip metadata directly from Timeline Track 1 (Camera Footage)
    clips = dr.get_timeline_clips()
    print(f"Total # of clips: {len(clips)}")

    # Create a working surface for the rendering
    surface, ctx = renderer.empty_frame()

    # Create ffmpeg pipeline
    ffmpeg = FFmpeg()

    # Loop through all clips on the timeline
    for idx, item in enumerate(clips):

        # Extract source timecodes & clip bounds directly
        media_pool_item = item.GetMediaPoolItem()
        if not media_pool_item:
            continue

        # Get the timecode of the clip
        clip_props = media_pool_item.GetClipProperty()
        start_tc_str = clip_props.get("Start TC", "00:00:00:00")
        start_tc = TimeUtils.tc_to_seconds(start_tc_str, frame_rate)
        start_frame = item.GetStart()
        total_frames = item.GetDuration()    # Actual number of frames on timeline
        left_offset = item.GetLeftOffset()      # Trimmed starting offset in frames

        # Calculate the actual timecode after left trims
        trimmed_start_tc = start_tc + (left_offset / frame_rate)

        # Create the video sequence for this clip
        file_path = f"{output_path}/{output_prefix}{start_frame}.mov"
        ffmpeg.open(canvas_width, canvas_height, frame_rate, file_path)
        frame_count = 0

        # Loop through all individual video frames
        for frame_idx in range(total_frames): 

            # Calculate the drift-corrected timestamp for this frame
            t = drift_calc.clip_tc_to_true_gpx_epoch(
                start_tc=trimmed_start_tc,
                frame_idx=frame_idx
            )

            # Draw active dynamic widgets on template
            renderer.draw_frame(ctx, t)

            # Output the generated frame to the destination file
            ffmpeg.write(surface.get_data())

            frame_count += 1
            print(f"Clip {idx + 1}: {frame_count} of {total_frames} frames\r", end='', flush=True)
        
        # Close output video file
        print()
        ffmpeg.close()

        # Import and place rendered clip on timeline
        dr.import_and_place_overlay(
            file_path=file_path,
            record_frame_start=start_frame,
            track_index=2
        )