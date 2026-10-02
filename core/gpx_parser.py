"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- GPX file parsing and coordinate-to-canvas mapping

Author: ghoss
License: MIT
===============================================================================
"""

import sys
import gpxpy


class GPXParser:

    """
    Parse GPX file and extract track points with time, lat/lon, and elevation.
    """
    def parse(self, gpx_file_path):

        try:
            with open(gpx_file_path, 'r', encoding='utf-8') as gpx_file:
                gpx = gpxpy.parse(gpx_file)

        except Exception as e:
            print(f"Failed to open GPX file: {e}")
            sys.exit(1)
        
        points = []
        prev_point = None
        cum_distance = 0.0
        first_timestamp = None
        last_valid_alt = None

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if point.time is not None:
                        # Convert time to timestamp
                        timestamp = int(point.time.timestamp())
                        if first_timestamp is None:
                            first_timestamp = timestamp
                            elapsed_time = 0
                        else:
                            elapsed_time = max(0, timestamp - first_timestamp)

                        # Calculate distance in metres to the previous point
                        if prev_point is not None:
                            cum_distance += point.distance_2d(prev_point)

                        # Set elevation to last valid altitude or None
                        if point.elevation is None:
                            point.elevation = last_valid_alt
                        else:
                            last_valid_alt = point.elevation

                        # Default extension values
                        hr = None
                        temp = None
                        cadence = None

                        # Parse extensions XML tree for sensor metrics
                        for ext in point.extensions:
                            # Find all child tags regardless of XML namespace prefix
                            for child in ext.iter():
                                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                                
                                if tag == 'hr' and child.text:
                                    try:
                                        hr = int(child.text)
                                    except ValueError:
                                        pass
                                elif tag == 'atemp' and child.text:
                                    try:
                                        temp = float(child.text)
                                    except ValueError:
                                        pass
                                elif tag == 'cad' and child.text:
                                    try:
                                        cadence = int(child.text)
                                    except ValueError:
                                        pass

                        points.append({
                            'time': timestamp,
                            'elapsed_time': elapsed_time,
                            'lat': point.latitude,
                            'lon': point.longitude,
                            'alt': point.elevation,
                            'distance': cum_distance,
                            'hr': hr,
                            'temp': temp,
                            'cadence': cadence
                        })

                        prev_point = point
        
        return points