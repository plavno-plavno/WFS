import os
import logging
import threading


class SRTWriter:
    """
    A thread-safe class to create and manage SRT (SubRip Subtitle) files with immediate writing.

    Args:
        output_file (str): The path to the SRT file to create or append to.
    """

    def __init__(self, output_file):
        self.output_file = output_file
        self.lock = threading.Lock()
        self.current_segment_number = 1

        # Determine the mode based on file existence
        if os.path.exists(self.output_file):
            self.mode = 'a'
            self.current_segment_number = self._get_last_segment_number() + 1
            logging.info(
                f"Appending to existing SRT file '{self.output_file}' starting at segment {self.current_segment_number}.")
        else:
            self.mode = 'w'
            logging.info(f"Creating new SRT file '{self.output_file}'.")

        try:
            # Open the file in the determined mode and keep it open
            self.srt_file = open(self.output_file, self.mode, encoding='utf-8')
            if self.mode == 'w':
                logging.info(f"Initialized new SRT file: {self.output_file}")
            else:
                logging.info(f"Opened existing SRT file for appending: {self.output_file}")
        except Exception as e:
            logging.error(f"Failed to open SRT file '{self.output_file}': {e}")
            raise

    def _get_last_segment_number(self):
        """
        Retrieves the last segment number from an existing SRT file.

        Returns:
            int: The last segment number. Returns 0 if the file is empty or improperly formatted.
        """
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                segment_numbers = [int(line.strip()) for line in lines if line.strip().isdigit()]
                if segment_numbers:
                    return max(segment_numbers)
        except Exception as e:
            logging.error(f"Error reading '{self.output_file}': {e}")
        return 0

    @staticmethod
    def format_time(seconds):
        """
        Converts time in seconds to SRT timestamp format.

        Args:
            seconds (float): Time in seconds.

        Returns:
            str: Formatted time string in 'HH:MM:SS,mmm' format.
        """
        millis = int((seconds - int(seconds)) * 1000)
        secs = int(seconds) % 60
        mins = (int(seconds) // 60) % 60
        hours = (int(seconds) // 3600)
        return f"{hours:02}:{mins:02}:{secs:02},{millis:03}"

    def add_segment(self, start, end, text):
        """
        Adds a single subtitle segment and writes it immediately to the SRT file.

        Args:
            start (float): Start time in seconds.
            end (float): End time in seconds.
            text (str): Subtitle text.

        Raises:
            ValueError: If start time is not less than end time.
        """
        if start >= end:
            raise ValueError("Start time must be less than end time.")

        segment = {
            'start': start,
            'end': end,
            'text': text.strip().replace('\n', ' ')  # Ensuring single-line text
        }

        with self.lock:
            try:
                start_time = self.format_time(float(segment['start']))
                end_time = self.format_time(float(segment['end']))
                formatted_text = segment['text']

                # Write the segment to the file
                self.srt_file.write(f"{self.current_segment_number}\n")
                self.srt_file.write(f"{start_time} --> {end_time}\n")
                self.srt_file.write(f"{formatted_text}\n\n")
                self.srt_file.flush()  # Ensure it's written to disk
                logging.debug(f"Wrote segment {self.current_segment_number} to '{self.output_file}'.")

                self.current_segment_number += 1
            except Exception as e:
                logging.error(f"Failed to write segment {self.current_segment_number} to '{self.output_file}': {e}")

    def add_segments(self, segments):
        """
        Adds multiple subtitle segments and writes them immediately to the SRT file.

        Args:
            segments (list of dict): A list where each dict contains 'start', 'end', and 'text' keys.
        """
        for segment in segments:
            self.add_segment(segment['start'], segment['end'], segment['text'])

    def close(self):
        """
        Closes the SRT file. Should be called when done writing to ensure the file is properly closed.
        """
        with self.lock:
            try:
                if not self.srt_file.closed:
                    self.srt_file.close()
                    logging.info(f"Closed SRT file '{self.output_file}'.")
            except Exception as e:
                logging.error(f"Failed to close SRT file '{self.output_file}': {e}")

    def __del__(self):
        """
        Destructor to ensure the SRT file is closed properly if not already done.
        """
        self.close()

    def __enter__(self):
        """
        Enter the runtime context related to this object.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context and close the file.
        """
        self.close()
