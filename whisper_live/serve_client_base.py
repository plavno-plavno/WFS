import json
import logging
import threading

import numpy as np


class ServeClientBase(object):
    RATE = 16000
    SERVER_READY = "SERVER_READY"
    DISCONNECT = "DISCONNECT"

    def __init__(self, client_uid, websocket, server):
        self.client_uid = client_uid
        self.websocket = websocket
        self.frames = b""
        self.timestamp_offset = 0.0
        self.frames_np = None
        self.frames_offset = 0.0
        self.text = []
        self.current_out = ''
        self.prev_out = ''
        self.t_start = None
        self.exit = False
        self.same_output_threshold = 0
        self.show_prev_out_thresh = 4  # if pause(no output from whisper) show previous output for 4 seconds
        self.add_pause_thresh = 0   # add a blank to segment list as a pause(no speech) for 2 seconds
        self.transcript = []
        self.send_last_n_segments = 10
        self.all_langs = None
        self.speaker_lang = None
        self.server = server
        self.index = '_9079dbe1_3b33_49d8_831b_bd75c70bfeca'

        # text formatting
        self.pick_previous_segments = 2

        # threading
        self.lock = threading.Lock()

    def speech_to_text(self):
        raise NotImplementedError

    def transcribe_audio(self):
        raise NotImplementedError

    def handle_transcription_output(self):
        raise NotImplementedError

    def set_speaker_lang(self, speaker_lang):
        if speaker_lang:
            self.speaker_lang = speaker_lang

    def set_index(self, index):
        if index:
            self.index = index

    def add_frames(self, frame_np):
        """
        Add audio frames to the ongoing audio stream buffer.

        This method is responsible for maintaining the audio stream buffer, allowing the continuous addition
        of audio frames as they are received. It also ensures that the buffer does not exceed a specified size
        to prevent excessive memory usage.

        If the buffer size exceeds a threshold (60 seconds of audio data), it discards the oldest 30 seconds
        of audio data to maintain a reasonable buffer size. If the buffer is empty, it initializes it with the provided
        audio frame. The audio stream buffer is used for real-time processing of audio data for transcription.

        Args:
            frame_np (numpy.ndarray): The audio frame data as a NumPy array.

        """
        self.lock.acquire()
        try:
            # If the buffer exists and exceeds 60 seconds:
            if self.frames_np is not None and self.frames_np.shape[0] > 60 * self.RATE:
                self.frames_offset += 30.0
                self.frames_np = self.frames_np[int(30 * self.RATE):]

                # Ensure timestamp_offset doesn't fall behind frames_offset
                if self.timestamp_offset < self.frames_offset:
                    self.timestamp_offset = self.frames_offset

            # If no buffer yet, initialize it with the new frame
            if self.frames_np is None:
                self.frames_np = frame_np.copy()
            else:
                # Otherwise, append the new frame to the existing buffer
                self.frames_np = np.concatenate((self.frames_np, frame_np), axis=0)
        finally:
            self.lock.release()

    def clip_audio_if_no_valid_segment(self):
        """
        Update the timestamp offset based on audio buffer status.
        Clip audio if the current chunk exceeds 30 seconds, this basically implies that
        no valid segment for the last 30 seconds from whisper
        """
        if self.frames_np[int((self.timestamp_offset - self.frames_offset) * self.RATE):].shape[0] > 25 * self.RATE:
            duration = self.frames_np.shape[0] / self.RATE
            self.timestamp_offset = self.frames_offset + duration - 5

    def get_audio_chunk_for_processing(self):
        """
        Retrieves the next chunk of audio data for processing based on the current offsets.

        Calculates which part of the audio data should be processed next, based on
        the difference between the current timestamp offset and the frame's offset, scaled by
        the audio sample rate (RATE). It then returns this chunk of audio data along with its
        duration in seconds.

        Returns:
            tuple: A tuple containing:
                - input_bytes (np.ndarray): The next chunk of audio data to be processed.
                - duration (float): The duration of the audio chunk in seconds.
        """
        samples_take = max(0, (self.timestamp_offset - self.frames_offset) * self.RATE)
        input_bytes = self.frames_np[int(samples_take):].copy()
        duration = input_bytes.shape[0] / self.RATE
        return input_bytes, duration

    def prepare_segments(self, last_segment=None):
        """
        Prepares the segments of transcribed text to be sent to the client.

        This method compiles the recent segments of transcribed text, ensuring that only the
        specified number of the most recent segments are included. It also appends the most
        recent segment of text if provided (which is considered incomplete because of the possibility
        of the last word being truncated in the audio chunk).

        Args:
            last_segment (str, optional): The most recent segment of transcribed text to be added
                                          to the list of segments. Defaults to None.

        Returns:
            list: A list of transcribed text segments to be sent to the client.
        """
        segments = []
        if len(self.transcript) >= self.send_last_n_segments:
            segments = self.transcript[-self.send_last_n_segments:].copy()
        else:
            segments = self.transcript.copy()
        if last_segment is not None:
            segments = segments + [last_segment]
        return segments

    def get_audio_chunk_duration(self, input_bytes):
        """
        Calculates the duration of the provided audio chunk.

        Args:
            input_bytes (numpy.ndarray): The audio chunk for which to calculate the duration.

        Returns:
            float: The duration of the audio chunk in seconds.
        """
        return input_bytes.shape[0] / self.RATE

    def send_transcription_to_client(self, segments):
        """
        Sends the specified transcription segments to the client over the websocket connection.

        Formats the transcription segments into a JSON object and attempts to send
        this object to the client and to all listeners. If an error occurs, it logs the error.

        Args:
            segments (list): A list of transcription segments to be sent to the client.
        """
        message = {
            "uid": self.client_uid,
            "segments": segments,
        }        
                
        try:            
            # Send to the primary client
            self.websocket.send(json.dumps(message))
            print(f"[INFO]     Sent transcription to [CLIENT]: {message}")

        except Exception as e:
            logging.error('[ERROR SEND TRANSCRIPTION TO CLIENT CONNECTION BROKEN]',)
            client = self.server.speaker_manager.get_client(self.websocket)
            if client and not isinstance(client, bool):
                print('Trying to CLEAN UP')
                client.stop_and_destroy_thread()
                client.cleanup()
            else:
               logging.warning('Client is not an object')


    def send_text_answer_to_client(self, text:str):
        """
        Sends the specified text answer to the client over the websocket connection.

        Formats the text answer into a JSON object and attempts to send
        this object to the client and to all listeners. If an error occurs, it logs the error.

        Args:
            text (str): RAG answer to be sent to the client.
        """
        message = {
            "uid": self.client_uid,
            "text": text,
        }        
            
        try:            
            # Send to the primary client
            self.websocket.send(json.dumps(message))
            print(f"[INFO]     Sent RAG text answer to [CLIENT]: {message}")

        except Exception as e:
            logging.error('[ERROR SEND RAG ANSWER TO CLIENT CONNECTION BROKEN]',)
            client = self.server.speaker_manager.get_client(self.websocket)
            if client and not isinstance(client, bool):
                print('Trying to CLEAN UP')
                client.stop_and_destroy_thread()
                client.cleanup()
            else:
               logging.warning('Client is not an object')


            

    def disconnect(self):
        """
        Notify the client of disconnection and send a disconnect message.

        This method sends a disconnect message to the client via the WebSocket connection to notify them
        that the transcription service is disconnecting gracefully.

        """
        self.websocket.send(json.dumps({
            "uid": self.client_uid,
            "message": self.DISCONNECT
        }))

    def cleanup(self):
        """
        Perform cleanup tasks before exiting the transcription service.

        This method performs necessary cleanup tasks, including stopping the transcription thread, marking
        the exit flag to indicate the transcription thread should exit gracefully, and destroying resources
        associated with the transcription process.

        """
        print("Cleaning up.")
        self.exit = True