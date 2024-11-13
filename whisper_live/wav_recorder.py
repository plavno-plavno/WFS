import os
import shutil
import wave
import threading
import json
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import numpy as np


class WavRecorder:
    """
    A class for handling audio chunks, saving them as WAV files, and uploading
    fully recorded files to an Amazon S3 bucket asynchronously.

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
        self.frames = b""
        self.n_audio_file = 0

        # S3 Configuration
        self.s3_bucket = s3_bucket
        self.s3_access_key = s3_access_key
        self.s3_secret_key = s3_secret_key
        self.s3_region = s3_region
        self.s3_prefix = s3_prefix.strip('/')

        if self.save_output_recording:
            # Prepare a directory for saving chunks
            if os.path.exists("chunks"):
                shutil.rmtree("chunks")
            os.makedirs("chunks")

            # Initialize S3 client
            if not all([self.s3_bucket, self.s3_access_key, self.s3_secret_key, self.s3_region]):
                raise ValueError("S3 credentials and bucket information must be provided when save_output_recording is True.")
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key,
                region_name=self.s3_region
            )

    def process_audio_chunk(self, audio_chunk):
        """
        Process and save an incoming audio chunk.

        Args:
            audio_chunk (bytes): The audio chunk to process.
        """
        self.frames += audio_chunk

        # Save frames if they exceed the size for one chunk (e.g., 1 minute of audio)
        if len(self.frames) > 60 * self.rate * 2:  # 2 bytes per sample
            if self.save_output_recording:
                self.save_chunk(self.n_audio_file)
                self.n_audio_file += 1
            self.frames = b""

    def save_chunk(self, n_audio_file):
        """
        Save the current audio frames to a WAV file.

        Args:
            n_audio_file (int): The index for the WAV file.
        """
        file_path = f"chunks/{n_audio_file}.wav"
        self.write_audio_frames_to_file(self.frames[:], file_path)
        logging.info(f"Saved chunk to {file_path}")

    def finalize_recording(self):
        """
        Finalize recording by saving remaining frames and combining chunks if enabled.
        Upload the final file to S3 if configured.
        """
        if self.save_output_recording and len(self.frames):
            self.save_chunk(self.n_audio_file)
            self.n_audio_file += 1

        if self.save_output_recording:
            self.write_output_recording(self.n_audio_file)
            self.upload_to_s3(self.output_recording_filename)

    def write_audio_frames_to_file(self, frames, file_name):
        """
        Write audio frames to a WAV file.

        Args:
            frames (bytes): The audio frames to be written.
            file_name (str): The name of the WAV file.
        """
        with wave.open(file_name, "wb") as wavfile:
            wavfile.setnchannels(self.channels)
            wavfile.setsampwidth(2)  # 16-bit audio
            wavfile.setframerate(self.rate)
            wavfile.writeframes(frames)

    def write_output_recording(self, n_audio_file):
        """
        Combine all saved chunks into a single WAV file.

        Args:
            n_audio_file (int): The number of chunks to combine.
        """
        input_files = [
            f"chunks/{i}.wav" for i in range(n_audio_file) if os.path.exists(f"chunks/{i}.wav")
        ]
        with wave.open(self.output_recording_filename, "wb") as wavfile:
            wavfile.setnchannels(self.channels)
            wavfile.setsampwidth(2)
            wavfile.setframerate(self.rate)
            for in_file in input_files:
                with wave.open(in_file, "rb") as wav_in:
                    while True:
                        data = wav_in.readframes(self.chunk_size)
                        if data == b"":
                            break
                        wavfile.writeframes(data)
                os.remove(in_file)
                logging.info(f"Combined and removed chunk {in_file}")
        logging.info(f"Final recording saved to {self.output_recording_filename}")

        # Clean up temporary directory to store chunks
        if os.path.exists("chunks"):
            shutil.rmtree("chunks")

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


