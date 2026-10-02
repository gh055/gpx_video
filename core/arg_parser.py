"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Command line argument and nested JSON configuration parsing

Author: ghoss
License: MIT
===============================================================================
"""

import sys
import os
import argparse
import tomllib


"""
Parse command line arguments and merge them with nested JSON configuration.

Returns:
    tuple: (args_namespace, config_dict)
        - args_namespace: Flat CLI flags (gpx_file, output_path, info, etc.)
        - config_dict: Full nested layout dictionary (canvas, widgets, etc.)
"""
def parse_arguments():

    parser = argparse.ArgumentParser(
        description="Generate transparent MOV video overlay from GPX track using widget layouts."
    )

    # Core CLI arguments
    parser.add_argument('--config', type=str, required=True, help='Path to JSON layout configuration file')
    parser.add_argument('--gpx-file', type=str, required=False, help='Path to GPX track file (overrides JSON config if provided)')
    parser.add_argument('--output-path', type=str, default=None, help='Output directory for rendered video file')
    parser.add_argument('--info', action=argparse.BooleanOptionalAction, default=False, help='Show GPS and clip info only')
    parser.add_argument('--tc-offset', type=int, default=None, help='Video clip TC offset in frames to sync with GPX track')

    args = parser.parse_args()

    # Load nested JSON configuration file
    if not os.path.exists(args.config):
        print(f"Error: Configuration file '{args.config}' not found.")
        sys.exit(1)

    try:
        with open(args.config, 'rb') as f:
            config = tomllib.load(f)

    except Exception as e:
        print(f"Error parsing configuration file '{args.config}': {e}")
        sys.exit(1)

    # Merge / Override top-level values if explicit CLI options are supplied
    if args.gpx_file:
        config['gpx_file'] = args.gpx_file
    elif 'gpx_file' not in config:
        print("Error: GPX file path must be specified via '--gpx-file' CLI flag or 'gpx_file' key in JSON config.")
        sys.exit(1)

    if args.output_path:
        config['output_path'] = args.output_path
    elif 'output_path' not in config:
        config['output_path'] = '.'

    if args.tc_offset:
        config['tc_offset'] = args.tc_offset
    elif 'tc_offset' not in config:
        config['tc_offset'] = 0

    return args, config