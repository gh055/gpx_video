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
import tempfile
import os


class FFmpeg:

    def __init__(self):

        self.log_file = None
        self.process = None


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
        
        # Create a temporary file to store FFmpeg's log output
        self.log_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log')

        try:
            # Start FFmpeg process with stdin for input
            # FFmpeg sends logs to stderr, stdout can go to DEVNULL
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=self.log_file
            )

        except Exception as e:
            print(f"FFmpeg Error: {e}.")
            self._cleanup_log()
            sys.exit(1)


    """
    Write a frame to the current output file
    """
    def write(self, frame_data):

        try:
            # Ensure we're sending complete frame data
            if len(frame_data) == self.expected_frame_length:
                # RGBA = 4 bytes per pixel
                self.process.stdin.write(frame_data)
            else:
                print(f"Warning: Frame size mismatch. Expected {self.expected_frame_length}, got {len(frame_data)}")

        except BrokenPipeError:
            # Get FFmpeg output for debugging
            self._print_error_log_and_exit()

        except Exception as e:
            print(f"Error writing frame data: {e}")
            self._print_error_log_and_exit()


    """
    Close frame generation pipeline for current file
    """
    def close(self):

        if self.process and self.process.stdin:
            self.process.stdin.close()
            
        return_code = self.process.wait()
        
        if return_code != 0:
            print(f"FFmpeg exited with error code {return_code}")
            self._print_error_log_and_exit()

        # Cleanup temporary file on success
        self._cleanup_log()


    """
    Reads log content, outputs it to console, cleans up the file, and exits.
    """
    def _print_error_log_and_exit(self):

        if self.log_file:

            self.log_file.flush()

            try:
                with open(self.log_file.name, 'r') as f:
                    logs = f.read()
                if logs.strip():
                    print("FFmpeg error output:\n", logs, file=sys.stderr)

            except Exception as e:
                print(f"Failed to read FFmpeg log file: {e}", file=sys.stderr)

            finally:
                self._cleanup_log()

        sys.exit(1)


    """
    Closes and removes the temporary log file.
    """
    def _cleanup_log(self):

        if self.log_file:

            try:
                self.log_file.close()
                if os.path.exists(self.log_file.name):
                    os.remove(self.log_file.name)

            except Exception:
                pass

            self.log_file = None