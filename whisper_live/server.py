import os
import json
import functools
import ssl
import base64
import logging
import torch
from enum import Enum
from typing import List, Optional, Tuple

from whisper_live.transcriber import WhisperModel

import numpy as np

from websockets.sync.server import serve
from websockets.exceptions import ConnectionClosed

from df.enhance import enhance, init_df, load_audio, resample
from torch import Tensor
from torchaudio import AudioMetaData

from df.logger import warn_once

from whisper_live.client_managers import SpeakerManager, ListenerManager
from whisper_live.serve_client_base import ServeClientBase
from whisper_live.serve_client_faster_whisper import ServeClientFasterWhisper
from whisper_live.serve_listener import ServeListener
from translation_tools.llama.utils import LoadBalancedTranslator
from translation_tools.madlad400.translator import MultiLingualTranslatorLive


class BackendType(Enum):
    FASTER_WHISPER = "faster_whisper"

    @staticmethod
    def valid_types() -> List[str]:
        return [backend_type.value for backend_type in BackendType]

    @staticmethod
    def is_valid(backend: str) -> bool:
        return backend in BackendType.valid_types()

    def is_faster_whisper(self) -> bool:
        return self == BackendType.FASTER_WHISPER



class TranscriptionServer:
    RATE = 16000

    def __init__(self):
        self.transcriber = None
        self.speaker_manager = SpeakerManager(max_clients=4)
        self.listener_manager = ListenerManager(max_clients=64)
        self.use_vad = True
        self.single_model = False
        USE_MADLAD = os.getenv("USE_MADLAD", "false").lower() == "true"
        if USE_MADLAD:
            self.translator = MultiLingualTranslatorLive()
        else:
            self.translator = LoadBalancedTranslator()
        
        # Load default DeepFilterNet model
        try:
            self.df_model, self.df_state, _ = init_df()
        except Exception as e:
            print('[ERROR]    Cannot download DeepFilterNet model.')
            self.df_model, self.df_state = None, None


    def initialize_client(self, websocket, options):
        if options.get("listener_uid"):
            # Initialize listener if 'is_listener' is set in options
            listener = ServeListener(
                websocket,
                client_uid=options.get('uid', ''),
                listener_uid=options.get('listener_uid', ''),
            )
            self.listener_manager.add_client(websocket, listener)
            
            logging.info("Initialized listener.")
            return  # Exit function to avoid client initialization for listeners

        # Initialize client if 'is_listener' is not set
        client: Optional[ServeClientBase] = None
        client = ServeClientFasterWhisper(
                websocket,
                language=options.get('language', None),
                task=options.get('task', "transcribe"),
                client_uid=options.get('uid', 'client-id-not-received'),
                model=options.get('model', "large-v3"),
                initial_prompt=options.get("initial_prompt"),
                vad_parameters=options.get("vad_parameters"),
                use_vad=self.use_vad,
                translator=self.translator,
                transcriber=self.transcriber,
                server=self
            )
        logging.info("Running faster_whisper backend.")
        if client is None:
            raise ValueError(f"Backend type {self.backend.value} not recognized or not handled.")
        self.speaker_manager.add_client(websocket, client)

    def get_audio_from_websocket(self, websocket):
        """
        Receives audio buffer from websocket and creates a numpy array from it.
        Args:
            websocket: The websocket to receive audio from.
        Returns:
            A numpy array containing the audio, or False in case of an error.
        """
        data = websocket.recv()
        if data == b"END_OF_AUDIO":
            return False, None, None
        if data == b"LISTENER":
            return True, None, None
        try:
            parsed_data = json.loads(data)
            speaker_lang = parsed_data.get('speakerLang')
            all_langs = parsed_data.get('allLangs')
            audio_base64 = parsed_data.get('audio')
            is_stream_started = parsed_data.get('isStartStream',True)

            if audio_base64:
                # Decode base64 to bytes
                audio_bytes = base64.b64decode(audio_base64)

                audio, _ = load_audio(audio_bytes, self.df_state.sr())
                enhanced = enhance(self.df_model, self.df_state, audio)
                enhanced = resample(enhanced, self.df_state.sr(), 16000)     # Resample to 16kHz
                audio_np = np.frombuffer(enhanced.numpy().tobytes(), dtype=np.float32)
                
                return audio_np, speaker_lang, all_langs, is_stream_started
            else:
                return False, None, None, None
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decoding Error: Unable to parse JSON data. Details: {str(e)}")
            return False, None, None, None
        except Exception as e:
            logging.error(f"An error occurred while processing audio: {str(e)}")
            return False, None, None, None

    def handle_new_connection(self, websocket):
        try:
            logging.info("New client connected")
            options = websocket.recv()
            options = json.loads(options)
            self.use_vad = options.get('use_vad')
            if self.speaker_manager.is_server_full(websocket, options):
                websocket.close()
                return False  # Indicates that the connection should not continue

            self.initialize_client(websocket, options)
            return True
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from client")
            return False
        except ConnectionClosed:
            logging.error("Connection closed by client")
            return False
        except Exception as e:
            logging.error(f"Error during new connection initialization: {str(e)}")
            return False

    def process_audio_frames(self, websocket):
        frame_np, speaker_lang, all_langs, is_stream_started = self.get_audio_from_websocket(websocket)
        if type(frame_np) == bool and frame_np:
            return True
        client = self.speaker_manager.get_client(websocket)

        if client is False or frame_np is False or frame_np is None or frame_np.size == 0:
            return False

        client.set_speaker_lang(speaker_lang)
        client.set_all_langs(all_langs)
        client.add_frames(frame_np)
        client.set_is_stream_started(is_stream_started)
        return True

    def recv_audio(
        self,
        websocket):
        """
        Receive audio chunks from a client in an infinite loop.

        Continuously receives audio frames from a connected client
        over a WebSocket connection. It processes the audio frames using a
        voice activity detection (VAD) model to determine if they contain speech
        or not. If the audio frame contains speech, it is added to the client's
        audio data for ASR.
        If the maximum number of clients is reached, the method sends a
        "WAIT" status to the client, indicating that they should wait
        until a slot is available.
        If a client's connection exceeds the maximum allowed time, it will
        be disconnected, and the client's resources will be cleaned up.

        Args:
            websocket (WebSocket): The WebSocket connection for the client.
            backend (str): The backend to run the server with.
            faster_whisper_custom_model_path (str): path to custom faster whisper model.


        Raises:
            Exception: If there is an error during the audio frame processing.
        """
        if not self.handle_new_connection(websocket):
            return

        try:
            while not self.speaker_manager.is_client_timeout(websocket):
                if not self.process_audio_frames(websocket):
                    break
        except ConnectionClosed:
            logging.info("Connection closed by client")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
        finally:
            if self.speaker_manager.get_client(websocket):
                self.cleanup(websocket)
                websocket.close()
            del websocket

    def configure_ssl(self, ssl_cert_file, ssl_key_file, ssl_passphrase):
        """
        Configure the SSL context based on the provided certificate and key files.

        Args:
            ssl_cert_file (str): Path to the SSL certificate file.
            ssl_key_file (str): Path to the SSL key file.
            ssl_passphrase (str): Optional passphrase for the SSL key.

        Returns:
            ssl_context: A configured SSL context or None if SSL is not configured.
        """
        ssl_context = None
        if ssl_cert_file and ssl_key_file:
            logging.info(f"SSL certificate found: {ssl_cert_file}")
            logging.info(f"SSL key found: {ssl_key_file}")
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(certfile=ssl_cert_file, keyfile=ssl_key_file, password=ssl_passphrase)
        return ssl_context

    def create_model(self,model_size_or_path):
        """
        Instantiates a new model, sets it as the transcriber.
        """

        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda":
            major, _ = torch.cuda.get_device_capability(device)
            compute_type = "float16" if major >= 7 else "float32"
        else:
            compute_type = "int8"

        logging.info(f"Using Device={device} with precision {compute_type}")
        self.transcriber = WhisperModel(
            model_size_or_path,
            device=device,
            compute_type=compute_type,
            local_files_only=False,
        )

    def run(self,
            host,
            port=9090,
            backend="faster_whisper",
            faster_whisper_custom_model_path=None,
            ssl_cert_file=None,
            ssl_key_file=None,
            ssl_passphrase=None,
            loop=None):
        """
        Run the transcription server with optional SSL support.

        Args:
            host (str): The host address to bind the server.
            port (int): The port number to bind the server.
            ssl_cert_file (str): Path to the SSL certificate file.
            ssl_key_file (str): Path to the SSL key file.
            ssl_passphrase (str): Optional passphrase for the SSL key.
        """

        if faster_whisper_custom_model_path is not None and not os.path.exists(faster_whisper_custom_model_path):
            raise ValueError(f"Custom faster_whisper model '{faster_whisper_custom_model_path}' is not a valid path.")

        self.create_model(faster_whisper_custom_model_path)

        if not BackendType.is_valid(backend):
            raise ValueError(f"{backend} is not a valid backend type. Choose backend from {BackendType.valid_types()}")

        # Configure SSL context using the new method
        ssl_context = self.configure_ssl(ssl_cert_file, ssl_key_file, ssl_passphrase)

        # Log the server availability
        if ssl_context:
            logging.info(f"Server will be available at: wss://{host}:{port}")
        else:
            logging.info(f"SSL not configured. Server will be available at: ws://{host}:{port}")

        # Start the server with SSL support if ssl_context is not None
        with serve(
                functools.partial(
                    self.recv_audio
                ),
                host,
                port,
                ssl=ssl_context  # Pass the SSL context if created
        ) as server:
            server.serve_forever()

    def cleanup(self, websocket):
        """
        Cleans up resources associated with a given client's websocket.

        Args:
            websocket: The websocket associated with the client to be cleaned up.
        """
        if self.speaker_manager.get_client(websocket):
            self.speaker_manager.remove_client(websocket)