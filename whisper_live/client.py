import os
import shutil
import wave

import logging
import numpy as np
import pyaudio
import threading
import json
import websocket
import uuid
import time
import ffmpeg
import whisper_live.utils as utils
import asyncio


class Client:
    INSTANCES = {}
    END_OF_AUDIO = "END_OF_AUDIO"

    def __init__(
        self,
        host=None,
        port=None,
        lang=None,
        translate=False,
        model="small",
        srt_file_path="output.srt",
        use_vad=True,
        log_transcription=True
    ):
        print("Client: __init__ called")
        self.recording = False
        self.task = "transcribe"
        self.uid = str(uuid.uuid4())
        self.waiting = False
        self.last_response_received = None
        self.disconnect_if_no_response_for = 15
        self.language = lang
        self.model = model
        self.server_error = False
        self.srt_file_path = srt_file_path
        self.use_vad = use_vad
        self.last_segment = None
        self.last_received_segment = None
        self.log_transcription = log_transcription

        if translate:
            self.task = "translate"

        self.audio_bytes = None

        if host is not None and port is not None:
            socket_url = f"ws://{host}:{port}"
            self.client_socket = websocket.WebSocketApp(
                socket_url,
                on_open=lambda ws: self.on_open(ws),
                on_message=lambda ws, message: self.on_message(ws, message),
                on_error=lambda ws, error: self.on_error(ws, error),
                on_close=lambda ws, close_status_code, close_msg: self.on_close(
                    ws, close_status_code, close_msg
                ),
            )
        else:
            print("[ERROR]: No host or port specified.")
            return

        Client.INSTANCES[self.uid] = self

        # start websocket client in a thread
        self.ws_thread = threading.Thread(target=self.client_socket.run_forever)
        self.ws_thread.setDaemon(True)
        self.ws_thread.start()

        self.transcript = []
        print("[INFO]: * recording")

    def handle_status_messages(self, message_data):
        """Handles server status messages."""
        print("Client: handle_status_messages called")
        status = message_data["status"]
        if status == "WAIT":
            self.waiting = True
            print(f"[INFO]: Server is full. Estimated wait time {round(message_data['message'])} minutes.")
        elif status == "ERROR":
            print(f"Message from Server: {message_data['message']}")
            self.server_error = True
        elif status == "WARNING":
            print(f"Message from Server: {message_data['message']}")

    def process_segments(self, segments):
        """Processes transcript segments."""
        print("Client: process_segments called")
        text = []
        for i, seg in enumerate(segments):
            if not text or text[-1] != seg["text"]:
                text.append(seg["text"])
                if i == len(segments) - 1:
                    self.last_segment = seg
                elif (self.server_backend == "faster_whisper" and
                      (not self.transcript or
                        float(seg['start']) >= float(self.transcript[-1]['end']))):
                    self.transcript.append(seg)
        # update last received segment and last valid response time
        if self.last_received_segment is None or self.last_received_segment != segments[-1]["text"]:
            self.last_response_received = time.time()
            self.last_received_segment = segments[-1]["text"]

        if self.log_transcription:
            # Truncate to last 3 entries for brevity.
            text = text[-3:]
            utils.clear_screen()
            utils.print_transcript(text)

    def on_message(self, ws, message):
        print("Client: on_message called")
        message = json.loads(message)

        if self.uid != message.get("uid"):
            print("[ERROR]: invalid client uid")
            return

        if "status" in message.keys():
            self.handle_status_messages(message)
            return

        if "message" in message.keys() and message["message"] == "DISCONNECT":
            print("[INFO]: Server disconnected due to overtime.")
            self.recording = False

        if "message" in message.keys() and message["message"] == "SERVER_READY":
            self.last_response_received = time.time()
            self.recording = True
            self.server_backend = message["backend"]
            print(f"[INFO]: Server Running with backend {self.server_backend}")
            return

        if "language" in message.keys():
            self.language = message.get("language")
            lang_prob = message.get("language_prob")
            print(
                f"[INFO]: Server detected language {self.language} with probability {lang_prob}"
            )
            return

        if "segments" in message.keys():
            self.process_segments(message["segments"])

    def on_error(self, ws, error):
        print("Client: on_error called")
        print(f"[ERROR] WebSocket Error: {error}")
        self.server_error = True
        self.error_message = error

    def on_close(self, ws, close_status_code, close_msg):
        print("Client: on_close called")
        print(f"[INFO]: Websocket connection closed: {close_status_code}: {close_msg}")
        self.recording = False
        self.waiting = False

    def on_open(self, ws):
        print("Client: on_open called")
        print("[INFO]: Opened connection")
        ws.send(
            json.dumps(
                {
                    "uid": self.uid,
                    "language": self.language,
                    "task": self.task,
                    "model": self.model,
                    "use_vad": self.use_vad
                }
            )
        )

    def send_packet_to_server(self, message):
        print("Client: send_packet_to_server called")
        try:
            self.client_socket.send(message, websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            print(e)

    def close_websocket(self):
        print("Client: close_websocket called")
        try:
            self.client_socket.close()
        except Exception as e:
            print("[ERROR]: Error closing WebSocket:", e)

        try:
            self.ws_thread.join()
        except Exception as e:
            print("[ERROR:] Error joining WebSocket thread:", e)

    def get_client_socket(self):
        print("Client: get_client_socket called")
        return self.client_socket

    def write_srt_file(self, output_path="output.srt"):
        print("Client: write_srt_file called")
        if self.server_backend == "faster_whisper":
            if (self.last_segment):
                self.transcript.append(self.last_segment)
            utils.create_srt_file(self.transcript, output_path)

    def wait_before_disconnect(self):
        print("Client: wait_before_disconnect called")
        """Waits a bit before disconnecting in order to process pending responses."""
        assert self.last_response_received
        while time.time() - self.last_response_received < self.disconnect_if_no_response_for:
            continue

    async def connect_and_listen(self,ws):
        try:
            self.ws = await ws.connect(self.ws_url)
            print("[INFO]: Connection established")

            while True:
                try:
                    # Try receiving a message from the WebSocket
                    resp = await self.websocket.recv()
                    print(f"[INFO]: Received message: {resp}")
                
                except ws.ConnectionClosed as e:
                    # Handle the disconnection
                    print(f"[ERROR]: Connection closed with error: {e}")
                    break

        except Exception as e:
            # If the connection couldn't be established initially
            print(f"[ERROR]: Could not connect to server: {e}")

        # Attempt to reconnect after disconnection
        print("[INFO]: Reconnecting...")
        await asyncio.sleep(5)  # Wait a bit before reconnecting
        await self.connect_and_listen()  # Try reconnecting recursively

    async def reconnect(self, ws_url):
        print("[INFO]: Reconnecting...")
        await asyncio.sleep(5)  # Wait before trying to reconnect
        await self.connect_and_listen(ws_url)  # Reconnect to the server

class TranscriptionTeeClient:
    def __init__(self, clients, save_output_recording=False, output_recording_filename="./output_recording.wav"):
        print("TranscriptionTeeClient: __init__ called")
        self.clients = clients
        if not self.clients:
            raise Exception("At least one client is required.")
        self.chunk = 4096
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.record_seconds = 60000
        self.save_output_recording = save_output_recording
        self.output_recording_filename = output_recording_filename
        self.frames = b""
        self.p = pyaudio.PyAudio()
        print("TranscriptionTeeClient: Audio stream initialization")
        try:
            self.stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
            )
            print("TranscriptionTeeClient: Audio stream opened")
        except OSError as error:
            print(f"[WARN]: Unable to access microphone. {error}")
            self.stream = None

    def __call__(self, audio=None, rtsp_url=None, hls_url=None, save_file=None):
        print(f"TranscriptionTeeClient: __call__ invoked with audio={audio}, rtsp_url={rtsp_url}, hls_url={hls_url}")
        assert sum(
            source is not None for source in [audio, rtsp_url, hls_url]
        ) <= 1, 'You must provide only one selected source'

        print("TranscriptionTeeClient: Waiting for server ready...")
        for client in self.clients:
            while not client.recording:
                if client.waiting or client.server_error:
                    self.close_all_clients()
                    return

        print("[INFO]: Server Ready!")
        if hls_url is not None:
            print("TranscriptionTeeClient: Processing HLS stream")
            self.process_hls_stream(hls_url, save_file)
        elif audio is not None:
            print("TranscriptionTeeClient: Resampling audio file")
            resampled_file = utils.resample(audio)
            self.play_file(resampled_file)
        elif rtsp_url is not None:
            print("TranscriptionTeeClient: Processing RTSP stream")
            self.process_rtsp_stream(rtsp_url)
        else:
            print("TranscriptionTeeClient: Starting recording")
            self.record()

    def close_all_clients(self):
        print("TranscriptionTeeClient: close_all_clients called")
        for client in self.clients:
            client.close_websocket()

    def write_all_clients_srt(self):
        print("TranscriptionTeeClient: write_all_clients_srt called")
        for client in self.clients:
            client.write_srt_file(client.srt_file_path)

    def multicast_packet(self, packet, unconditional=False):
        print("TranscriptionTeeClient: multicast_packet called")
        for client in self.clients:
            if unconditional or client.recording:
                client.send_packet_to_server(packet)

    def play_file(self, filename):
        print(f"TranscriptionTeeClient: play_file called with filename={filename}")
        with wave.open(filename, "rb") as wavfile:
            self.stream = self.p.open(
                format=self.p.get_format_from_width(wavfile.getsampwidth()),
                channels=wavfile.getnchannels(),
                rate=wavfile.getframerate(),
                input=True,
                output=True,
                frames_per_buffer=self.chunk,
            )
            try:
                while any(client.recording for client in self.clients):
                    data = wavfile.readframes(self.chunk)
                    if data == b"":
                        break

                    print("TranscriptionTeeClient: Sending audio data to clients")
                    audio_array = self.bytes_to_float_array(data)
                    self.multicast_packet(audio_array.tobytes())
                    self.stream.write(data)

                wavfile.close()

                for client in self.clients:
                    client.wait_before_disconnect()
                self.multicast_packet(Client.END_OF_AUDIO.encode('utf-8'), True)
                self.write_all_clients_srt()
                self.stream.close()
                self.close_all_clients()

            except KeyboardInterrupt:
                print("TranscriptionTeeClient: Keyboard interrupt detected")
                wavfile.close()
                self.stream.stop_stream()
                self.stream.close()
                self.p.terminate()
                self.close_all_clients()
                self.write_all_clients_srt()

    def process_rtsp_stream(self, rtsp_url):
        print(f"TranscriptionTeeClient: process_rtsp_stream called with rtsp_url={rtsp_url}")
        process = self.get_rtsp_ffmpeg_process(rtsp_url)
        self.handle_ffmpeg_process(process, stream_type='RTSP')

    def process_hls_stream(self, hls_url, save_file):
        print(f"TranscriptionTeeClient: process_hls_stream called with hls_url={hls_url}")
        process = self.get_hls_ffmpeg_process(hls_url, save_file)
        self.handle_ffmpeg_process(process, stream_type='HLS')

    def handle_ffmpeg_process(self, process, stream_type):
        print(f"TranscriptionTeeClient: handle_ffmpeg_process called for {stream_type} stream")
        stderr_thread = threading.Thread(target=self.consume_stderr, args=(process,))
        stderr_thread.start()
        try:
            while True:
                in_bytes = process.stdout.read(self.chunk * 2)  # 2 bytes per sample
                if not in_bytes:
                    break
                print(f"TranscriptionTeeClient: Received {len(in_bytes)} bytes from {stream_type}")
                audio_array = self.bytes_to_float_array(in_bytes)
                self.multicast_packet(audio_array.tobytes())

        except Exception as e:
            print(f"[ERROR]: Failed to connect to {stream_type} stream: {e}")
        finally:
            self.close_all_clients()
            self.write_all_clients_srt()
            if process:
                process.kill()

        print(f"[INFO]: {stream_type} stream processing finished.")

    def get_rtsp_ffmpeg_process(self, rtsp_url):
        print(f"TranscriptionTeeClient: get_rtsp_ffmpeg_process called with rtsp_url={rtsp_url}")
        return (
            ffmpeg
            .input(rtsp_url, threads=0)
            .output('-', format='s16le', acodec='pcm_s16le', ac=1, ar=self.rate)
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )

    def get_hls_ffmpeg_process(self, hls_url, save_file):
        print(f"TranscriptionTeeClient: get_hls_ffmpeg_process called with hls_url={hls_url}")
        if save_file is None:
            process = (
                ffmpeg
                .input(hls_url, threads=0)
                .output('-', format='s16le', acodec='pcm_s16le', ac=1, ar=self.rate)
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
        else:
            input = ffmpeg.input(hls_url, threads=0)
            output_file = input.output(save_file, acodec='copy', vcodec='copy').global_args('-loglevel', 'quiet')
            output_std = input.output('-', format='s16le', acodec='pcm_s16le', ac=1, ar=self.rate)
            process = (
                ffmpeg.merge_outputs(output_file, output_std)
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
        return process

    def consume_stderr(self, process):
        print(f"TranscriptionTeeClient: consume_stderr called for process")
        for line in iter(process.stderr.readline, b""):
            logging.debug(f'[STDERR]: {line.decode()}')

    def save_chunk(self, n_audio_file):
        print(f"TranscriptionTeeClient: save_chunk called for file {n_audio_file}")
        t = threading.Thread(
            target=self.write_audio_frames_to_file,
            args=(self.frames[:], f"chunks/{n_audio_file}.wav",),
        )
        t.start()

    def finalize_recording(self, n_audio_file):
        print(f"TranscriptionTeeClient: finalize_recording called for chunk {n_audio_file}")
        if self.save_output_recording and len(self.frames):
            self.write_audio_frames_to_file(
                self.frames[:], f"chunks/{n_audio_file}.wav"
            )
            n_audio_file += 1
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.close_all_clients()
        if self.save_output_recording:
            self.write_output_recording(n_audio_file)
        self.write_all_clients_srt()

    def record(self):
        print("TranscriptionTeeClient: record called")
        n_audio_file = 0
        if self.save_output_recording:
            if os.path.exists("chunks"):
                shutil.rmtree("chunks")
            os.makedirs("chunks")
        try:
            for _ in range(0, int(self.rate / self.chunk * self.record_seconds)):
                if not any(client.recording for client in self.clients):
                    print("TranscriptionTeeClient: No active clients, stopping recording")
                    break
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames += data

                print(f"TranscriptionTeeClient: Received {len(data)} bytes of audio data")
                audio_array = self.bytes_to_float_array(data)

                self.multicast_packet(audio_array.tobytes())

                if len(self.frames) > 60 * self.rate:
                    if self.save_output_recording:
                        self.save_chunk(n_audio_file)
                        n_audio_file += 1
                    self.frames = b""
            self.write_all_clients_srt()

        except KeyboardInterrupt:
            print("TranscriptionTeeClient: Keyboard interrupt, finalizing recording")
            self.finalize_recording(n_audio_file)

    def write_audio_frames_to_file(self, frames, file_name):
        print(f"TranscriptionTeeClient: write_audio_frames_to_file called for file {file_name}")
        with wave.open(file_name, "wb") as wavfile:
            wavfile: wave.Wave_write
            wavfile.setnchannels(self.channels)
            wavfile.setsampwidth(2)
            wavfile.setframerate(self.rate)
            wavfile.writeframes(frames)

    def write_output_recording(self, n_audio_file):
        print(f"TranscriptionTeeClient: write_output_recording called for {n_audio_file} files")
        input_files = [
            f"chunks/{i}.wav"
            for i in range(n_audio_file)
            if os.path.exists(f"chunks/{i}.wav")
        ]
        with wave.open(self.output_recording_filename, "wb") as wavfile:
            wavfile: wave.Wave_write
            wavfile.setnchannels(self.channels)
            wavfile.setsampwidth(2)
            wavfile.setframerate(self.rate)
            for in_file in input_files:
                with wave.open(in_file, "rb") as wav_in:
                    while True:
                        data = wav_in.readframes(self.chunk)
                        if data == b"":
                            break
                        wavfile.writeframes(data)
                # remove this file
                os.remove(in_file)
        wavfile.close()
        if os.path.exists("chunks"):
            shutil.rmtree("chunks")

    @staticmethod
    def bytes_to_float_array(audio_bytes):
        print("TranscriptionTeeClient: bytes_to_float_array called")
        raw_data = np.frombuffer(buffer=audio_bytes, dtype=np.int16)
        return raw_data.astype(np.float32) / 32768.0


class TranscriptionClient(TranscriptionTeeClient):
    def __init__(
        self,
        host,
        port,
        lang=None,
        translate=False,
        model="small",
        use_vad=True,
        save_output_recording=False,
        output_recording_filename="./output_recording.wav",
        output_transcription_path="./output.srt",
        log_transcription=True,
    ):
        print("TranscriptionClient: __init__ called")
        self.client = Client(host, port, lang, translate, model, srt_file_path=output_transcription_path, use_vad=use_vad, log_transcription=log_transcription)
        print("TranscriptionClient: Client initialized")
        
        if save_output_recording and not output_recording_filename.endswith(".wav"):
            raise ValueError(f"Please provide a valid `output_recording_filename`: {output_recording_filename}")
        if not output_transcription_path.endswith(".srt"):
            raise ValueError(f"Please provide a valid `output_transcription_path`: {output_transcription_path}. The file extension should be `.srt`.")
        
        print("TranscriptionClient: Validating file paths")
        TranscriptionTeeClient.__init__(
            self,
            [self.client],
            save_output_recording=save_output_recording,
            output_recording_filename=output_recording_filename
        )
        print("TranscriptionClient: TranscriptionTeeClient initialized")
