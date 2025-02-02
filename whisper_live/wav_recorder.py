import os
import wave
import threading
import json
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import numpy as np

class WavRecorder:
    """
    A class for handling audio chunks, saving them as a single WAV file, and uploading
    the final recorded file to an Amazon S3 bucket asynchronously.

    Args:
        save_output_recording (bool): Whether to save the output recording to a file.
        output_recording_filename (str): The file name for the final output WAV file.
        s3_bucket (str): The name of the S3 bucket to upload files to.
        s3_access_key (str): AWS access key ID.
        s3_secret_key (str): AWS secret access key.
        s3_region (str): AWS region where the S3 bucket is located.
        s3_prefix (str, optional): Prefix (folder path) in the S3 bucket. Defaults to ''.
    """
    def __init__(
        self,
        save_output_recording=False,
        output_recording_filename="./output_recording.wav",
        s3_bucket=None,
        s3_access_key=None,
        s3_secret_key=None,
        s3_region=None,
        s3_prefix=''
    ):
        self.chunk_size = 4096
        self.channels = 1
        self.rate = 16000
        self.save_output_recording = save_output_recording
        self.output_recording_filename = output_recording_filename
        self.frames = []
        self.is_recording = False

        # S3 Configuration
        self.s3_bucket = s3_bucket
        self.s3_access_key = s3_access_key
        self.s3_secret_key = s3_secret_key
        self.s3_region = s3_region
        self.s3_prefix = s3_prefix.strip('/')

        # Initialize S3 client if saving is enabled
        if self.save_output_recording:
            if not all([self.s3_bucket, self.s3_access_key, self.s3_secret_key, self.s3_region]):
                raise ValueError("S3 credentials and bucket information must be provided when save_output_recording is True.")
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key,
                region_name=self.s3_region
            )
            # Open the WAV file for writing
            self.wav_file = wave.open(self.output_recording_filename, "wb")
            self.wav_file.setnchannels(self.channels)
            self.wav_file.setsampwidth(2)  # 16-bit audio
            self.wav_file.setframerate(self.rate)
            logging.info(f"Initialized WAV file {self.output_recording_filename} for recording.")

    def process_audio_chunk(self, audio_chunk):
        """
        Process and save an incoming audio chunk by writing it directly to the WAV file.

        Args:
            audio_chunk (bytes): The audio chunk to process.
        """
        if self.save_output_recording and self.wav_file:
            try:
                self.wav_file.writeframes(audio_chunk)
                logging.debug(f"Written audio chunk of size {len(audio_chunk)} bytes to {self.output_recording_filename}.")
            except Exception as e:
                logging.error(f"Failed to write audio chunk to WAV file: {e}")

        # Optionally, accumulate frames in memory (if needed for other purposes)
        self.frames.append(audio_chunk)

    def finalize_recording(self):
        """
        Finalize recording by closing the WAV file and uploading it to S3 if configured.
        """
        if self.save_output_recording:
            try:
                if self.wav_file:
                    self.wav_file.close()
                    logging.info(f"Finalized and closed WAV file {self.output_recording_filename}.")
            except Exception as e:
                logging.error(f"Failed to close WAV file: {e}")

            # Upload the final WAV file to S3
            self.upload_to_s3(self.output_recording_filename)

    def upload_to_s3(self, file_path):
        """
        Upload a file to the configured S3 bucket using a separate thread.

        Args:
            file_path (str): The path to the file to upload.
        """
        thread = threading.Thread(target=self._upload_file_to_s3, args=(file_path,))
        thread.start()
        logging.info(f"Started upload thread for {file_path}")

    def _upload_file_to_s3(self, file_path):
        """
        The worker function to upload a file to S3.

        Args:
            file_path (str): The path to the file to upload.
        """
        try:
            file_name = os.path.basename(file_path)
            s3_key = f"{self.s3_prefix}/{file_name}" if self.s3_prefix else file_name
            self.s3_client.upload_file(file_path, self.s3_bucket, s3_key)
            logging.info(f"Successfully uploaded {file_path} to s3://{self.s3_bucket}/{s3_key}")
        except (BotoCoreError, ClientError) as e:
            logging.error(f"Failed to upload {file_path} to S3: {e}")

    @staticmethod
    def bytes_to_float_array(audio_bytes):
        """
        Convert audio data from bytes to a NumPy float array.

        Args:
            audio_bytes (bytes): Audio data in bytes.

        Returns:
            np.ndarray: Normalized audio data as a NumPy array.
        """
        raw_data = np.frombuffer(buffer=audio_bytes, dtype=np.int16)
        return raw_data.astype(np.float32) / 32768.0

    def __del__(self):
        """
        Destructor to ensure the WAV file is closed properly if not already done.
        """
        if self.save_output_recording and self.wav_file:
            try:
                self.wav_file.close()
                logging.info(f"Closed WAV file {self.output_recording_filename} in destructor.")
            except Exception as e:
                logging.error(f"Failed to close WAV file in destructor: {e}")
