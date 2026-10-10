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


class DaVinciResolveSession:

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
            self.media_pool = project.GetMediaPool()
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
    Returns selected clips on the timeline if any exist; 
    otherwise falls back to returning all clips on the specified track.
    """
    def get_timeline_clips(self, track_type = 'video', track_index = 1):

        # Get all selected items on the track from the timeline
        all_selected_items = self.timeline.GetSelectedClips()
        
        # Filter items by video type
        selected_video_items = [
            item for item in all_selected_items 
            if (item.GetTrackTypeAndIndex() == [track_type, track_index])
        ]

        # Return selected items if present; otherwise fall back to all items on track
        if selected_video_items:
            return selected_video_items
        else:
            return self.timeline.GetItemListInTrack(track_type, track_index)


    """
    Imports the rendered overlay MOV into the Media Pool and places it
    onto the specified track at record_frame_start.
    """
    def import_and_place_overlay(self, file_path, record_frame_start, track_index = 2):

            # Import rendered clip to Media Pool
            imported_items = self.media_pool.ImportMedia([file_path])

            if not imported_items:
                print(f"Failed to import: {file_path}")
                return None
            
            media_item = imported_items[0]

            # Add clip to timeline on the higher track
            clip_info = {
                "mediaPoolItem": media_item,
                "startFrame": record_frame_start,
                "recordFrame": record_frame_start,
                "trackIndex": track_index
            }
            
            # AppendToTimeline creates timeline entries using clip specification dictionaries
            result = self.media_pool.AppendToTimeline([clip_info])
            return result