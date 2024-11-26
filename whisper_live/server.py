import os
import json
import functools
import ssl
import base64
import logging
from enum import Enum
from typing import List, Optional

import numpy as np

from websockets.sync.server import serve
from websockets.exceptions import ConnectionClosed

from whisper_live.client_managers import SpeakerManager, ListenerManager
from whisper_live.serve_client_base import ServeClientBase
from whisper_live.serve_client_faster_whisper import ServeClientFasterWhisper
from whisper_live.serve_listener import ServeListener

from translation_tools.cerebras.translator import CerebrasTranslator
logging.basicConfig(level=logging.ERROR)


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
        self.speaker_manager = SpeakerManager()
        self.listener_manager = ListenerManager()
        self.use_vad = True
        self.single_model = False
        self.translator =  CerebrasTranslator()

    def initialize_client(
            self, websocket, options, faster_whisper_custom_model_path):

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
        if self.backend.is_faster_whisper():
            if faster_whisper_custom_model_path and os.path.exists(faster_whisper_custom_model_path):
                logging.info(f"Using custom model {faster_whisper_custom_model_path}")
                options["model"] = faster_whisper_custom_model_path

            client = ServeClientFasterWhisper(
                websocket,
                language=options.get('language', 'en'),
                task=options.get('task', "transcribe"),
                client_uid=options.get('uid', 'client-id-not-received'),
                model=options.get('model', "large-v3"),
                initial_prompt=options.get("initial_prompt"),
                vad_parameters=options.get("vad_parameters"),
                use_vad=self.use_vad,
                single_model=self.single_model,
                translator=self.translator,
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
            if audio_base64:
                # Decode base64 to bytes
                audio_bytes = base64.b64decode(audio_base64)
                # Convert bytes to numpy array
                audio_np = np.frombuffer(audio_bytes, dtype=np.float32)
                return audio_np, speaker_lang, all_langs
            else:
                return False, None, None
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decoding Error: Unable to parse JSON data. Details: {str(e)}")
            return False, None, None
        except Exception as e:
            logging.error(f"An error occurred while processing audio: {str(e)}")
            return False, None, None

    def handle_new_connection(self, websocket, faster_whisper_custom_model_path):
        try:
            logging.info("New client connected")
            options = websocket.recv()
            options = json.loads(options)
            self.use_vad = options.get('use_vad')
            if self.speaker_manager.is_server_full(websocket, options):
                websocket.close()
                return False  # Indicates that the connection should not continue
            
            self.initialize_client(websocket, options, faster_whisper_custom_model_path)
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
        frame_np, speaker_lang, all_langs = self.get_audio_from_websocket(websocket)
        if type(frame_np) == bool and frame_np:
            return True
        client = self.speaker_manager.get_client(websocket)

        if frame_np is False or frame_np is None or frame_np.size == 0:
            return False
        
        client.set_speaker_lang(speaker_lang)
        client.set_all_langs(all_langs)
        client.add_frames(frame_np)
        return True

    def recv_audio(
        self,
        websocket,
        backend: BackendType = BackendType.FASTER_WHISPER,
        faster_whisper_custom_model_path=None):
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
        self.backend = backend
        if not self.handle_new_connection(websocket, faster_whisper_custom_model_path):
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

    def run(self,
            host,
            port=9090,
            backend="faster_whisper",
            faster_whisper_custom_model_path=None,
            single_model=False,
            ssl_cert_file=None,
            ssl_key_file=None,
            ssl_passphrase=None):
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

        if single_model:
            if faster_whisper_custom_model_path:
                logging.info("Custom model option was provided. Switching to single model mode.")
                self.single_model = True
            else:
                logging.info("Single model mode currently only works with custom models.")

        if not BackendType.is_valid(backend):
            raise ValueError(f"{backend} is not a valid backend type. Choose backend from {BackendType.valid_types()}")

        # Create SSL context if SSL parameters are provided

        if ssl_cert_file and ssl_key_file:
            logging.info(f"SSL certificate found: {ssl_cert_file}")
            logging.info(f"SSL key found: {ssl_key_file}")
            logging.info(f"Server will be available at: wss://{host}:{port}")
        else:
            logging.info(f"SSL not configured. Server will be available at: ws://{host}:{port}")
            
        ssl_context = None
        if ssl_cert_file and ssl_key_file:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(certfile=ssl_cert_file, keyfile=ssl_key_file, password=ssl_passphrase)

        # Start the server with SSL support if ssl_context is not None
        with serve(
                functools.partial(
                    self.recv_audio,
                    backend=BackendType(backend),
                    faster_whisper_custom_model_path=faster_whisper_custom_model_path,
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