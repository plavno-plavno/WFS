import os
import time
import threading
import json
import logging
from enum import Enum
from typing import List, Optional
import torch
import numpy as np
from whisper_live.vad import VoiceActivityDetector
from whisper_live.transcriber import WhisperModel
from socketify import WebSocket,App  # Import WebSocket from Socketify
import copy

logging.basicConfig(level=logging.INFO)

class ClientManager:
    def __init__(self, max_clients=4, max_connection_time=600):
        #print("ClientManager: __init__ called")
        self.clients = {}
        self.start_times = {}
        self.max_clients = max_clients
        self.max_connection_time = max_connection_time
        #print(f"ClientManager initialized with max_clients={max_clients} and max_connection_time={max_connection_time}")

    def add_client(self, ws: WebSocket, client):
        #print("ClientManager: add_client called")
        if ws.socket_data_id not in self.clients:
            #print(f"Adding new client with WebSocket id={id(ws)} and client uid={client.client_uid}")
            self.clients[ws.socket_data_id] = client
            self.start_times[ws.socket_data_id] = time.time()
        else:
            print(f"Client with WebSocket id={id(ws.app)} already exists")

    def get_client(self, ws: WebSocket):
        #print("ClientManager: get_client called", ws, self.clients)
        if ws.socket_data_id in self.clients:
            #print(f"Client found for WebSocket id={id(ws.app)}, client uid={self.clients[ws].client_uid}")
            return self.clients[ws.socket_data_id]
        #print(f"Client not found for WebSocket id={id(ws.app)}")
        return False

    def remove_client(self, ws: WebSocket):
        #print("ClientManager: remove_client called")
        client = self.clients.pop(ws, None)
        if client:
            #print(f"Removing client with WebSocket id={id(ws.app)} and client uid={client.client_uid}")
            client.cleanup()
        else:
            print(f"No client found for WebSocket id={id(ws.app)} to remove")
        self.start_times.pop(ws, None)

    def get_wait_time(self):
        #print("ClientManager: get_wait_time called")
        wait_time = None
        for ws, start_time in self.start_times.items():
            current_client_time_remaining = self.max_connection_time - (time.time() - start_time)
            #print(f"Client with WebSocket id={id(ws)} has {current_client_time_remaining} seconds remaining")
            if wait_time is None or current_client_time_remaining < wait_time:
                wait_time = current_client_time_remaining
        calculated_wait_time = wait_time / 60 if wait_time is not None else 0
        #print(f"Calculated wait time: {calculated_wait_time} minutes")
        return calculated_wait_time

    def is_server_full(self, ws: WebSocket, options):
        #print("ClientManager: is_server_full called")
        current_client_count = len(self.clients)
        #print(f"Current client count: {current_client_count}, Max clients allowed: {self.max_clients}")
        if current_client_count >= self.max_clients:
            wait_time = self.get_wait_time()
            #print(f"Server is full. Sending WAIT message to client with uid={options['uid']}, wait time={wait_time}")
            response = {"uid": options["uid"], "status": "WAIT", "message": wait_time}
            ws.send(json.dumps(response))  # Use Socketify WebSocket send method
            return True
        #print("Server is not full. Client can proceed.")
        return False

    def is_client_timeout(self, ws: WebSocket):
        #print("ClientManager: is_client_timeout called")
        if ws not in self.start_times:
            #print(f"WebSocket id={id(ws)} does not exist in start_times")
            return False
        
        elapsed_time = time.time() - self.start_times[ws]
        #print(f"Elapsed time for client with WebSocket id={id(ws)}: {elapsed_time} seconds")
        
        if elapsed_time >= self.max_connection_time:
            #print(f"Client with WebSocket id={id(ws)} has timed out.")
            if ws in self.clients:
                #print(f"Disconnecting client with uid={self.clients[ws].client_uid} due to timeout")
                self.clients[ws].disconnect()
            self.remove_client(ws)
            return True
        
        #print(f"Client with WebSocket id={id(ws)} has not timed out yet.")
        return False


class BackendType(Enum):
    FASTER_WHISPER = "faster_whisper"

    @staticmethod
    def valid_types() -> List[str]:
        """
        Returns a list of valid backend types.

        Returns:
            List[str]: List of valid backend type values.
        """
        return [backend_type.value for backend_type in BackendType]

    @staticmethod
    def is_valid(backend: str) -> bool:
        """
        Checks if a given backend string is a valid type.

        Args:
            backend (str): The backend string to check.

        Returns:
            bool: True if the backend is valid, False otherwise.
        """
        return backend in BackendType.valid_types()

    def is_faster_whisper(self) -> bool:
        """
        Checks if the current backend is FASTER_WHISPER.

        Returns:
            bool: True if the current backend is FASTER_WHISPER.
        """
        return self == BackendType.FASTER_WHISPER
    


class TranscriptionServer:
    RATE = 16000

    def __init__(self):
        #print("TranscriptionServer: __init__ called")
        self.client_manager = ClientManager()
        self.no_voice_activity_chunks = 0
        self.use_vad = True
        self.single_model = False
        #print("TranscriptionServer initialized with VAD =", self.use_vad, "and single_model =", self.single_model)

    def initialize_client(self, ws, options, faster_whisper_custom_model_path):
        #print("TranscriptionServer: initialize_client called")
        #print(f"Initializing client for WebSocket id={id(ws)} with options={options}")
        client: Optional[ServeClientBase] = None

        if self.backend.is_faster_whisper():
            if faster_whisper_custom_model_path is not None and os.path.exists(faster_whisper_custom_model_path):
                pass
                #logging.info(f"Using custom model {faster_whisper_custom_model_path}")
                options["model"] = faster_whisper_custom_model_path
            client = ServeClientFasterWhisper(
                ws,
                language=options["language"],
                task=options["task"],
                client_uid=options["uid"],
                model=options["model"],
                initial_prompt=options.get("initial_prompt"),
                vad_parameters=options.get("vad_parameters"),
                use_vad=self.use_vad,
                single_model=self.single_model,
            )
            pass
            #logging.info("Running faster_whisper backend.")
            #print(f"Client initialized with faster_whisper backend for WebSocket id={id(ws)}")

        if client is None:
            raise ValueError(f"Backend type {self.backend.value} not recognized or not handled.")

        self.client_manager.add_client(ws, client)
        #print(f"Client added to ClientManager for WebSocket id={id(ws)}")

    def handle_new_connection(self, ws, options, faster_whisper_custom_model_path):
        #print("TranscriptionServer: handle_new_connection called")
        #print(f"Handling new connection for WebSocket id={id(ws)} with options={options}")
        try:
            pass
            #logging.info("New client connected")
            self.use_vad = options.get('use_vad')
            #print(f"VAD option set to {self.use_vad}")

            if self.client_manager.is_server_full(ws, options):
                #print(f"Server is full, closing connection for WebSocket id={id(ws)}")
                ws.close()
                return False  # Indicates that the connection should not continue

            # Initialize client after getting options
            self.initialize_client(ws, options, faster_whisper_custom_model_path)
            return True
        except json.JSONDecodeError:
            pass
            #logging.error("Failed to decode JSON from client")
            #print(f"JSON decoding failed for WebSocket id={id(ws)}")
            return False
        except Exception as e:
            pass
            #logging.error(f"Error during new connection initialization: {str(e)}")
            #print(f"Error initializing new connection for WebSocket id={id(ws)}: {str(e)}")
            return False

    def process_audio_frames(self, ws, frame_data):
        #print("TranscriptionServer: process_audio_frames called")
        #print(f"Processing audio frames for WebSocket id={id(ws)}, frame data length={len(frame_data)}")
        client = self.client_manager.get_client(ws)
        #logging.info(f"Received frame data of length: {len(frame_data)}")
        
        # Check if frame_data is valid
        if frame_data is False or frame_data is None or len(frame_data) == 0:
            #logging.error('Frame data is invalid or empty, no audio data received.')
            #print(f"Invalid or empty frame data received for WebSocket id={id(ws)}")
            return False

        # Process the frame data
        #logging.info(f"Processing {len(frame_data)} bytes of audio data")
        print(f"Adding frames for processing for WebSocket id={client}")
        client.add_frames(frame_data)
        return True

    def recv_audio(
        self, 
        ws, 
        message,  # The incoming message is passed here
        backend: BackendType = BackendType.FASTER_WHISPER, 
        faster_whisper_custom_model_path=None
    ):
        #print("TranscriptionServer: recv_audio called")
        #print(f"Receiving audio or control messages for WebSocket id={id(ws)}")
        self.backend = backend
        try:
            pass
            #logging.info('Message received in recv_audio')
            pass
            #logging.info(f'Message type: {type(message)}')
            pass
            #logging.info(f'Message content:')
            #print(f"Message type: {type(message)}, content: ")

            # Handle dict control messages (initial connection, options, etc.)
            if isinstance(message, dict):
                pass
                #logging.info('Processing JSON message (dict)')
                #print(f"Processing JSON message for WebSocket id={id(ws)}")
                # Pass the message to the initialization logic
                if not self.handle_new_connection(ws, message, faster_whisper_custom_model_path):
                    pass
                    #logging.error('Failed to handle new connection')
                    #print(f"Failed to handle new connection for WebSocket id={id(ws)}")
                    return

            # Handle binary audio data
            elif isinstance(message, bytes):
                pass
                #logging.info('Processing audio data')
                #print(f"Processing audio data for WebSocket id={id(ws)}, message size={len(message)} bytes")
                if not self.client_manager.is_client_timeout(ws):
                    pass
                    #logging.info('Client is active')
                    #print(f"Client is active for WebSocket id={id(ws)}")
                    if not self.process_audio_frames(ws, message):
                        #logging.error('Failed to process audio frames')
                        #print(f"Failed to process audio frames for WebSocket id={id(ws)}")
                        return
                else:
                    pass
                    #logging.info('Client timeout detected.')
                    #print(f"Client timeout detected for WebSocket id={id(ws)}")
        except Exception as e:
            logging.error(f"Unexpected error in recv_audio: {str(e)}")
            #print(f"Unexpected error in recv_audio for WebSocket id={id(ws)}: {str(e)}")
        
        finally:
            if self.client_manager.get_client(ws):
                print(222, self.client_manager.get_client(ws))
                #logging.info('Cleaning up connection')
                #print(f"Cleaning up connection for WebSocket id={id(ws)}")
                # self.cleanup(ws)
                # ws.close()
                #print(f"Connection closed for WebSocket id={id(ws)}")

    def cleanup(self, ws):
        #print("TranscriptionServer: cleanup called")
        #print(f"Cleaning up client for WebSocket id={id(ws)}")
        if self.client_manager.get_client(ws):
            self.client_manager.remove_client(ws)
            #print(f"Client removed for WebSocket id={id(ws)}")



class ServeClientBase(object):
    RATE = 16000
    SERVER_READY = "SERVER_READY"
    DISCONNECT = "DISCONNECT"

    def __init__(self, client_uid, websocket):
        #print("ServeClientBase: __init__ called")
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
        self.show_prev_out_thresh = 5   # if pause (no output from whisper), show previous output for 5 seconds
        self.add_pause_thresh = 3       # add a blank to segment list as a pause (no speech) for 3 seconds
        self.transcript = []
        self.send_last_n_segments = 10

        # text formatting
        self.pick_previous_segments = 2

        # threading
        self.lock = threading.Lock()
        #print(f"ServeClientBase initialized with client_uid={client_uid}")

    def speech_to_text(self):
        #print("ServeClientBase: speech_to_text called")
        raise NotImplementedError("speech_to_text method must be implemented by subclass")

    def transcribe_audio(self):
        #print("ServeClientBase: transcribe_audio called")
        raise NotImplementedError("transcribe_audio method must be implemented by subclass")

    def handle_transcription_output(self):
        #print("ServeClientBase: handle_transcription_output called")
        raise NotImplementedError("handle_transcription_output method must be implemented by subclass")

    def add_frames(self, frame_np):
        #print("ServeClientBase: add_frames called")
        self.lock.acquire()
        #print("Lock acquired for adding frames")
        if self.frames_np is not None:
            arr = np.frombuffer(self.frames_np, dtype=np.uint8)
        if self.frames_np is not None and arr.shape[0] > 45 * self.RATE:
            #print(f"Trimming audio buffer. Original frames size: {self.frames_np.shape[0]}")
            self.frames_offset += 30.0
            self.frames_np = self.frames_np[int(30 * self.RATE):]
            pass
            #logging.info(f"Audio buffer trimmed, new offset: {self.frames_offset}")
            #print(f"New frames size after trimming: {self.frames_np.shape[0]}")
            
            # Check if the timestamp offset is smaller than the frames offset (implies no speech)
            if self.timestamp_offset < self.frames_offset:
                #print(f"Updating timestamp_offset from {self.timestamp_offset} to {self.frames_offset}")
                self.timestamp_offset = self.frames_offset
        
        if self.frames_np is None:
            #print("Initializing frames_np")
            self.frames_np = copy.copy(frame_np)
        else:
            #print("Concatenating new frames to frames_np")
            self.frames_np = np.concatenate((self.frames_np, frame_np), axis=0)
        
        pass
        #logging.info(f"Total frames size after adding: {self.frames_np.shape[0]}")
        #print(f"Total frames size after adding: {self.frames_np.shape[0]}")
        self.lock.release()
        #print("Lock released after adding frames")

    def clip_audio_if_no_valid_segment(self):
        #print("ServeClientBase: clip_audio_if_no_valid_segment called")
        # Clip audio if current chunk exceeds 30 seconds and no valid segment was found
        arr = np.frombuffer(self.frames_np, dtype=np.uint8)
        if arr[int((self.timestamp_offset - self.frames_offset) * self.RATE):].shape[0] > 25 * self.RATE:
            duration = arr.shape[0] / self.RATE
            #print(f"Clipping audio. Duration={duration} seconds, frames_offset={self.frames_offset}, timestamp_offset={self.timestamp_offset}")
            self.timestamp_offset = self.frames_offset + duration - 5
            #print(f"Updated timestamp_offset after clipping: {self.timestamp_offset}")

    def get_audio_chunk_for_processing(self):
        #print("ServeClientBase: get_audio_chunk_for_processing called")
        # Get the audio chunk starting from the current offset for processing
        samples_take = max(0, (self.timestamp_offset - self.frames_offset) * self.RATE)
        input_bytes = copy.copy(self.frames_np[int(samples_take):])
        arr = np.frombuffer(input_bytes, dtype=np.uint8)
        duration = arr.shape[0] / self.RATE
        #print(f"Extracted audio chunk of {duration} seconds for processing")
        return input_bytes, duration

    def prepare_segments(self, last_segment=None):
        #print("ServeClientBase: prepare_segments called")
        # Prepare the most recent transcription segments to send to the client
        segments = []
        if len(self.transcript) >= self.send_last_n_segments:
            segments = copy.copy(self.transcript[-self.send_last_n_segments:])
        else:
            segments = copy.copy(self.transcript)
        if last_segment is not None:
            segments = segments + [last_segment]
        #print(f"Prepared {len(segments)} segments for sending")
        return segments

    def get_audio_chunk_duration(self, input_bytes):
        #print("ServeClientBase: get_audio_chunk_duration called")
        # Calculate the duration of the audio chunk
        arr = np.frombuffer(input_bytes, dtype=np.uint8)
        duration = arr.shape[0] / self.RATE
        #print(f"Calculated duration of audio chunk: {duration} seconds")
        return duration

    def send_transcription_to_client(self, segments):
        #print("ServeClientBase: send_transcription_to_client called")
        # Send transcription segments to the client via the websocket
        try:
            self.websocket.send(json.dumps({
                "uid": self.client_uid,
                "segments": segments,
            }))
            #print(f"Successfully sent {len(segments)} segments to client {self.client_uid}")
        except Exception as e:
            pass
            #logging.error(f"[ERROR]: Failed to send data to client {self.client_uid}: {e}")
            #print(f"[ERROR]: Failed to send data to client {self.client_uid}: {e}")

    def disconnect(self):
        #print("ServeClientBase: disconnect called")
        # Notify client of disconnection and send the disconnect message
        try:
            self.websocket.send(json.dumps({
                "uid": self.client_uid,
                "message": self.DISCONNECT
            }))
            #print(f"Client {self.client_uid} disconnected")
        except Exception as e:
            pass
            #logging.error(f"[ERROR]: Failed to notify disconnection for client {self.client_uid}: {e}")
            #print(f"[ERROR]: Failed to notify disconnection for client {self.client_uid}: {e}")

    def cleanup(self):
        #print("ServeClientBase: cleanup called")
        # Cleanup resources for the client
        pass
        #logging.info(f"Cleaning up client {self.client_uid}")
        self.exit = True
        #print(f"Cleanup completed for client {self.client_uid}")


class ServeClientFasterWhisper(ServeClientBase):

    SINGLE_MODEL = None
    SINGLE_MODEL_LOCK = threading.Lock()

    def __init__(self, websocket, task="transcribe", device=None, language=None, client_uid=None, model="small.en",
                 initial_prompt=None, vad_parameters=None, use_vad=True, single_model=False):
        #print("ServeClientFasterWhisper: __init__ called")
        super().__init__(client_uid, websocket)
        self.model_sizes = [
            "tiny", "tiny.en", "base", "base.en", "small", "small.en",
            "medium", "medium.en", "large-v2", "large-v3",
        ]
        if not os.path.exists(model):
            self.model_size_or_path = self.check_valid_model(model)
        else:
            self.model_size_or_path = model
        self.language = "en" if self.model_size_or_path.endswith("en") else language
        self.task = task
        self.initial_prompt = initial_prompt
        self.vad_parameters = vad_parameters or {"threshold": 0.5}
        self.no_speech_thresh = 0.45

        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda":
            major, _ = torch.cuda.get_device_capability(device)
            self.compute_type = "float16" if major >= 7 else "float32"
        else:
            self.compute_type = "int8"

        if self.model_size_or_path is None:
            return
            pass
        #logging.info(f"Using Device={device} with precision {self.compute_type}")

        if single_model:
            if ServeClientFasterWhisper.SINGLE_MODEL is None:
                self.create_model(device)
                ServeClientFasterWhisper.SINGLE_MODEL = self.transcriber
            else:
                self.transcriber = ServeClientFasterWhisper.SINGLE_MODEL
        else:
            self.create_model(device)

        self.use_vad = use_vad

        # threading
        self.trans_thread = threading.Thread(target=self.speech_to_text)
        self.trans_thread.start()
        self.websocket.send(
            json.dumps(
                {
                    "uid": self.client_uid,
                    "message": self.SERVER_READY,
                    "backend": "faster_whisper"
                }
            )
        )

    def create_model(self, device):
        #print("ServeClientFasterWhisper: create_model called")
        self.transcriber = WhisperModel(
            self.model_size_or_path,
            device=device,
            compute_type=self.compute_type,
            local_files_only=True,
        )

    def check_valid_model(self, model_size):
        #print("ServeClientFasterWhisper: check_valid_model called")
        if model_size not in self.model_sizes:
            self.websocket.send(
                json.dumps(
                    {
                        "uid": self.client_uid,
                        "status": "ERROR",
                        "message": f"Invalid model size {model_size}. Available choices: {self.model_sizes}"
                    }
                )
            )
            return None
        return model_size

    def set_language(self, info):
        #print("ServeClientFasterWhisper: set_language called")
        if info.language_probability > 0.5:
            self.language = info.language
            pass
            #logging.info(f"Detected language {self.language} with probability {info.language_probability}")
            self.websocket.send(json.dumps(
                {"uid": self.client_uid, "language": self.language, "language_prob": info.language_probability}))

    def transcribe_audio(self, input_sample):
        # print("ServeClientFasterWhisper: transcribe_audio called")
        if ServeClientFasterWhisper.SINGLE_MODEL:
            ServeClientFasterWhisper.SINGLE_MODEL_LOCK.acquire()
        

        result, info = self.transcriber.transcribe(
            input_sample,
            initial_prompt=self.initial_prompt,
            language=self.language,
            task=self.task,
            vad_filter=self.use_vad,
            vad_parameters=self.vad_parameters if self.use_vad else None)
        
        print(334444)
        if ServeClientFasterWhisper.SINGLE_MODEL:
            ServeClientFasterWhisper.SINGLE_MODEL_LOCK.release()

        if self.language is None and info is not None:
            self.set_language(info)
        return result

    def get_previous_output(self):
        #print("ServeClientFasterWhisper: get_previous_output called")
        segments = []
        if self.t_start is None:
            self.t_start = time.time()
        if time.time() - self.t_start < self.show_prev_out_thresh:
            segments = self.prepare_segments()

        # add a blank if there is no speech for 3 seconds
        if len(self.text) and self.text[-1] != '':
            if time.time() - self.t_start > self.add_pause_thresh:
                self.text.append('')
        return segments

    def handle_transcription_output(self, result, duration):
        #print("ServeClientFasterWhisper: handle_transcription_output called")
        segments = []
        if len(result):
            self.t_start = None
            last_segment = self.update_segments(result, duration)
            segments = self.prepare_segments(last_segment)
        else:
            # show previous output if there is pause i.e. no output from whisper
            segments = self.get_previous_output()

        if len(segments):
            self.send_transcription_to_client(segments)

    def speech_to_text(self):
        #print("ServeClientFasterWhisper: speech_to_text called")
        while True:
            if self.exit:
                #logging.info("Exiting speech to text thread")
                break

            if self.frames_np is None:
                continue

            self.clip_audio_if_no_valid_segment()

            input_bytes, duration = self.get_audio_chunk_for_processing()
            if duration < 1.0:
                time.sleep(0.1)     # wait for audio chunks to arrive
                continue
            try:
                input_sample = input_bytes[:]
                result = self.transcribe_audio(input_sample)

                print('---- result', result)

                if result is None or self.language is None:
                    self.timestamp_offset += duration
                    time.sleep(0.25)    # wait for voice activity, result is None when no voice activity
                    continue
                self.handle_transcription_output(result, duration)

            except Exception as e:
                logging.error(f"[ERROR]: Failed to transcribe audio chunk: {e}")
                time.sleep(0.01)

    def format_segment(self, start, end, text):
        #print("ServeClientFasterWhisper: format_segment called")
        return {
            'start': "{:.3f}".format(start),
            'end': "{:.3f}".format(end),
            'text': text
        }

    def update_segments(self, segments, duration):
        #print("ServeClientFasterWhisper: update_segments called")
        offset = None
        self.current_out = ''
        last_segment = None

        # process complete segments
        if len(segments) > 1:
            for i, s in enumerate(segments[:-1]):
                text_ = s.text
                self.text.append(text_)
                start, end = self.timestamp_offset + s.start, self.timestamp_offset + min(duration, s.end)

                if start >= end:
                    continue
                if s.no_speech_prob > self.no_speech_thresh:
                    continue

                self.transcript.append(self.format_segment(start, end, text_))
                offset = min(duration, s.end)

        # only process the segments if it satisfies the no_speech_thresh
        if segments[-1].no_speech_prob <= self.no_speech_thresh:
            self.current_out += segments[-1].text
            last_segment = self.format_segment(
                self.timestamp_offset + segments[-1].start,
                self.timestamp_offset + min(duration, segments[-1].end),
                self.current_out
            )

        # if same incomplete segment is seen multiple times then update the offset
        # and append the segment to the list
        if self.current_out.strip() == self.prev_out.strip() and self.current_out != '':
            self.same_output_threshold += 1
        else:
            self.same_output_threshold = 0

        if self.same_output_threshold > 5:
            if not len(self.text) or self.text[-1].strip().lower() != self.current_out.strip().lower():
                self.text.append(self.current_out)
                self.transcript.append(self.format_segment(
                    self.timestamp_offset,
                    self.timestamp_offset + duration,
                    self.current_out
                ))
            self.current_out = ''
            offset = duration
            self.same_output_threshold = 0
            last_segment = None
        else:
            self.prev_out = self.current_out

        # update offset
        if offset is not None:
            self.timestamp_offset += offset

        return last_segment
