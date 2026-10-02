"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- FFmpeg output routines

Author: ghoss
License: MIT
===============================================================================
"""

import sys
import subprocess


class FFmpeg:

    """
    Open the ffmpeg pipeline for subsequent frame output to a destination file
    """
    def open(self, canvas_width, canvas_height, frame_rate, output_file):

        # Calculate expected data length once for ffmpeg_write_frame
        self.expected_frame_length = canvas_width * canvas_height * 4

        # Generate FFmpeg command for transparent MOV output
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file without asking
            '-f', 'rawvideo',
            '-pix_fmt', 'bgra',
            '-s', f'{canvas_width}x{canvas_height}',
            '-r', str(frame_rate),
            '-i', '-',  # Input from stdin
            '-c:v', 'prores_ks',
            '-profile:v', '4',  # Profile 4 = ProRes 4444 (supports Alpha)
            '-pix_fmt', 'yuva444p10le',
            output_file
        ]
        
        try:
            # Start FFmpeg process with stdin for input
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            )

        except Exception as e:
            print(f"FFmpeg Error: {e}.")
            sys.exit(1)


    """
    Write a frame to the current output file
    """
    def write(self, frame_data):

        try:
            # Ensure we're sending complete frame data
            if len(frame_data) == self.expected_frame_length:  # RGBA = 4 bytes per pixel
                self.process.stdin.write(frame_data)
            else:
                print(f"Warning: Frame size mismatch. Expected {self.expected_frame_length}, got {len(frame_data)}")

        except BrokenPipeError:
            # Get FFmpeg output for debugging
            stderr_output, stdout_output = self.process.communicate()
            print("FFmpeg output:", stdout_output.decode())
            print("FFmpeg error output:", stderr_output.decode())
            sys.exit(1)

        except Exception as e:
            print(f"Error writing frame data: {e}")
            sys.exit(1)


    """
    Close frame generation pipeline for current file
    """
    def close(self):

        self.process.stdin.close()
        return_code = self.process.wait()
        
        if return_code != 0:
            stderr_output, stdout_output = self.process.communicate()
            print("FFmpeg error output:", stderr_output.decode())
            sys.exit(1)