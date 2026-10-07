"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Davinci Resolve API Interface integration

Author: ghoss
License: MIT
===============================================================================
"""

import sys
import DaVinciResolveScript as dvr_script


class DaVinci:

    """
    Get project details from currently open Davinci Resolve session
    """
    def __init__(self):

        # Connect to running DaVinci Resolve Studio instance
        try:
            resolve = dvr_script.scriptapp("Resolve")

        except ImportError:
            print("Could not find Davinci Resolve API")
            sys.exit(1)

        # Get Davinci project details
        if resolve:
            projectManager = resolve.GetProjectManager()
            project = projectManager.GetCurrentProject()
            self.timeline = project.GetCurrentTimeline()
        else:
            print("Could not connect to Davinci Resolve (is it running?)")
            sys.exit(1)      

        if not self.timeline:
            print("Please open a timeline in Davinci Resolve first.")
            sys.exit(1)


    """
    Return video properties: canvas width, height, framerate
    """
    def get_video_props(self):

        tl = self.timeline
        canvas_width = int(tl.GetSetting("timelineResolutionWidth"))
        canvas_height = int(tl.GetSetting("timelineResolutionHeight"))
        frame_rate = float(tl.GetSetting("timelineFrameRate"))

        return canvas_width, canvas_height, frame_rate


    """
    Get clips on named video track
    """
    def get_timeline_clips(self, track_type = 'video', track_number = 1):

        return self.timeline.GetItemListInTrack(track_type, track_number)