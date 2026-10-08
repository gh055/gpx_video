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
    parser.add_argument('--tc-offset', type=int, default=None, help='Video clip TC offset in frames to sync with GPX track')

    args = parser.parse_args()

    # Load nested JSON configuration file
    if not os.path.exists(args.config):
        print(f"Error: Configuration file '{args.config}' not found.")
        sys.exit(1)

    try:
        with open(args.config, 'rb') as f:
            config = tomllib.load(f)
            main_cfg = config.get('main', {})

    except Exception as e:
        print(f"Error parsing configuration file '{args.config}': {e}")
        sys.exit(1)

    # Merge / Override top-level values if explicit CLI options are supplied
    if args.gpx_file:
        config.setdefault('gpx', {})['file'] = args.gpx_file
    elif 'file' not in config.get('gpx', {}):
        print("Error: GPX file path must be specified via '--gpx-file' CLI flag or 'gpx_file' key in JSON config.")
        sys.exit(1)

    if args.output_path:
        raw_path = args.output_path
    else:
        raw_path = main_cfg.get('output_path', '.')

    # Expand path (e.g. ~/...)
    config.setdefault('main', {})['output_path'] = os.path.expanduser(raw_path)

    return args, config