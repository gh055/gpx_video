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
import numpy as np

from core.time_utils import TimeUtils
from core.davinci_api import DaVinci
from core.arg_parser import parse_arguments
from core.gpx_parser import GPXParser
from core.renderer import OverlayRenderer
from core.ffmpeg import FFmpeg


"""
Main execution
"""
if __name__ == "__main__":

    # Parse command line arguments and config file
    args, config = parse_arguments()

    # Get current Davinci Resolve project details
    dr = DaVinci()

    # Get the project's video properties
    pr_canvas_width, pr_canvas_height, pr_frame_rate = dr.get_video_props()

    # Override video properties by config values if specified
    cfg_canvas = config.get("canvas", {})
    canvas_width = cfg_canvas.get("width", pr_canvas_width)
    canvas_height = cfg_canvas.get("height", pr_canvas_height)
    frame_rate = cfg_canvas.get("frame_rate", pr_frame_rate)
    tc_offset = config.get("tc_offset", 0)

    # Update config with actual canvas properties
    config['canvas'] = {
        'width': canvas_width,
        'height': canvas_height,
        'frame_rate': frame_rate
    }
    print(f"Using {canvas_width}x{canvas_height} canvas @ {frame_rate} fps.")

    # Read GPX file
    gpx = GPXParser()
    gpx_points = gpx.parse(config['gpx_file'])
    print(f"GPX file contains {len(gpx_points)} data points. Timecode offset is {tc_offset}s")

    # Initialize rendering engine
    renderer = OverlayRenderer(config)

    # Create preview .PNG and exit if output path points to an image file
    output_path = config['output_path']
    if output_path.lower().endswith(".png"):
        # Create a template with dummy values
        static_canvas = renderer.draw_template(gpx_points, True)
        renderer.export(static_canvas, output_path)
        sys.exit(0)

    else:
        # Create a template without dummy values for video generation
        static_canvas = renderer.draw_template(gpx_points, False)  

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
        date_created = clip_props.get("Date Created")
        start_tc = TimeUtils.dt_to_epoch(date_created) + tc_offset
        duration_frames = item.GetDuration()    # Actual duration on timeline
        left_offset = item.GetLeftOffset()      # Trimmed starting offset in frames

        # Calculate the actual timecode (in seconds) after trims
        trimmed_start_tc = start_tc + int(left_offset / frame_rate)

        if args.info:
            print(f"First GPX Time: {TimeUtils.epoch_to_dt(gpx_points[0]['time'])}")
            print(f"First Clip Time: {TimeUtils.epoch_to_dt(trimmed_start_tc)}")
            break

        # Create the video sequence for this clip
        ffmpeg.open(canvas_width, canvas_height, frame_rate, f"{output_path}/gpx{idx:04d}.mov")
        frame_count = 0

        # Loop through all individual video frames
        frame_times = np.linspace(trimmed_start_tc, trimmed_start_tc + (duration_frames / frame_rate), num=duration_frames)
        for t in frame_times:

            # Draw active dynamic widgets on template
            renderer.draw_frame(ctx, t)

            # Output the generated frame to the destination file
            ffmpeg.write(surface.get_data())

            frame_count += 1
            print(f"Clip {idx}: {frame_count} of {duration_frames} frames\r", end='', flush=True)
        
        # Close output video file
        print()
        ffmpeg.close()