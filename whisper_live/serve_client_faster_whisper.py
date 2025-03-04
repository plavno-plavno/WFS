import logging
import threading
import json
import time
import string
import asyncio

from whisper_live.serve_client_base import ServeClientBase
from whisper_live.sentence_accumulator import SentenceAccumulator

class ServeClientFasterWhisper(ServeClientBase):
    SINGLE_MODEL_LOCK = threading.Lock()

    def __init__(
            self, websocket,
            task="transcribe",
            language=None,
            client_uid=None,
            model="large-v3",
            initial_prompt=None,
            vad_parameters=None,
            use_vad=True,
            translator=None,
            transcriber=None,
            server=None
    ):
        """
        Initialize a ServeClient instance.
        The Whisper model is initialized based on the client's language and device availability.
        The transcription thread is started upon initialization. A "SERVER_READY" message is sent
        to the client to indicate that the server is ready.

        Args:
            websocket (WebSocket): The WebSocket connection for the client.
            task (str, optional): The task type, e.g., "transcribe." Defaults to "transcribe".
            device (str, optional): The device type for Whisper, "cuda" or "cpu". Defaults to None.
            language (str, optional): The language for transcription. Defaults to None.
            client_uid (str, optional): A unique identifier for the client. Defaults to None.
            model (str, optional): The whisper model size. Defaults to 'small.en'
            initial_prompt (str, optional): Prompt for whisper inference. Defaults to None.
        """
        super().__init__(client_uid, websocket, server)
        self.translator = translator
        self.transcriber = transcriber
        self.server = server
        self.language = language
        self.task = task
        self.initial_prompt = initial_prompt
        self.vad_parameters = vad_parameters or {"threshold": 0.5}
        self.no_speech_thresh = 0.45
        self.call_count = 0
        self.use_vad = use_vad
        self.is_stream_started = True
        self.sa = SentenceAccumulator()
        self.stop_event = threading.Event()
        self.previous_translation_accumulated_text = ""
        self.previous_segment_ready = False
        self.disable_sentence_cutter = False
        self.return_translated_segments = False
        self.translation_id = 1
        self.translation_accumulated_text = ''
        self.translation_start_time = "0.0"
        self.translation_end_time = "0.0"
        

        # threading
        self.trans_thread = threading.Thread(target=self.speech_to_text,daemon=True)
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



    def set_disable_sentence_cutter(self, flag):
        self.disable_sentence_cutter = flag

    def set_return_translated_segments(self,flag):
        self.return_translated_segments = flag

    def set_is_stream_started(self,flag):
        self.is_stream_started = flag

    def check_valid_model(self, model_size):
        """
        Check if it's a valid whisper model size.

        Args:
            model_size (str): The name of the model size to check.

        Returns:
            str: The model size if valid, None otherwise.
        """
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
        """
        Updates the language attribute based on the detected language information.

        Args:
            info (object): An object containing the detected language and its probability. This object
                        must have at least two attributes: `language`, a string indicating the detected
                        language, and `language_probability`, a float representing the confidence level
                        of the language detection.
        """
        if info.language_probability > 0.5:
            self.language = info.language
            logging.info(f"Detected language {self.language} with probability {info.language_probability}")
            self.websocket.send(json.dumps(
                {"uid": self.client_uid, "language": self.language, "language_prob": info.language_probability}))

    def transcribe_audio(self, input_sample):
        """
        Transcribes the provided audio sample using the configured transcriber instance.
        ...

        Returns:
            The transcription result from the transcriber.
        """

        ServeClientFasterWhisper.SINGLE_MODEL_LOCK.acquire()

        result, info = self.transcriber.transcribe(
            input_sample,
            initial_prompt=self.initial_prompt,
            language=self.speaker_lang if self.speaker_lang else self.language,
            task=self.task,
            vad_filter=self.use_vad,
            vad_parameters=self.vad_parameters if self.use_vad else None)

        ServeClientFasterWhisper.SINGLE_MODEL_LOCK.release()

        if self.language is None and info is not None:
            self.set_language(info)
        return result

    def get_previous_output(self):
        """
        Retrieves previously generated transcription outputs if no new transcription is available
        from the current audio chunks.

        Checks the time since the last transcription output and, if it is within a specified
        threshold, returns the most recent segments of transcribed text. It also manages
        adding a pause (blank segment) to indicate a significant gap in speech based on a defined
        threshold.

        Returns:
            segments (list): A list of transcription segments. This may include the most recent
                            transcribed text segments or a blank segment to indicate a pause
                            in speech.
        """
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
        """
        Handle the transcription output, updating the transcript.

        Args:
            result (str): The result from whisper inference i.e. the list of segments.
            duration (float): Duration of the transcribed audio chunk.
        """

        if len(result):
            self.t_start = None
            last_segment = self.update_segments(result, duration)

            segments = self.prepare_segments(last_segment)
        else:
            # show previous output if there is pause i.e. no output from whisper
            segments = self.get_previous_output()

        if len(segments):
            self.send_transcription_to_client(segments)

    def translate_and_send_thread(self):
        translations = self.prepare_translations()
        if self.is_stream_started:
            self.send_translations_to_all_listeners(translations)
            if self.return_translated_segments:
                print('Translations to speaker')
                print(translations)
                self.send_transcription_to_client(translations)

    def speech_to_text(self):
        """
        Process an audio stream in an infinite loop, continuously transcribing the speech.

        This method continuously receives audio frames, performs real-time transcription, and sends
        transcribed segments to the client via a WebSocket connection.

        If the client's language is not detected, it waits for 30 seconds of audio input to make a language prediction.
        It utilizes the Whisper ASR model to transcribe the audio, continuously processing and streaming results. Segments
        are sent to the client in real-time, and a history of segments is maintained to provide context.Pauses in speech
        (no output from Whisper) are handled by showing the previous output for a set duration. A blank segment is added if
        there is no speech for a specified duration to indicate a pause.

        Raises:
            Exception: If there is an issue with audio processing or WebSocket communication.

        """
        while not self.stop_event.is_set():
            if self.exit:
                logging.info("Exiting speech to text thread")
                break

            if self.frames_np is None:
                continue

            client = self.server.speaker_manager.get_client(self.websocket)
            if not client:
                print("CLIENT DEAD")
                return

            self.clip_audio_if_no_valid_segment()

            input_bytes, duration = self.get_audio_chunk_for_processing()
            if duration < 1.0:
                time.sleep(0.1)  # wait for audio chunks to arrive
                continue
            try:
                input_sample = input_bytes.copy()
                result = self.transcribe_audio(input_sample)
                if result is None and self.translation_accumulated_text != "":
                    print(f"[INFO]: No output from Whisper, using previous output: {self.translation_accumulated_text}")
                    translation_thread = threading.Thread(target=self.translate_and_send_thread, daemon=True)
                    translation_thread.start()

                if result is None or self.language is None:
                    self.timestamp_offset += duration
                    time.sleep(0.25)  # wait for voice activity, result is None when no voice activity
                    continue
                self.handle_transcription_output(result, duration)

            except Exception as e:
                logging.error(f"[ERROR]: Failed to transcribe audio chunk: {e}")
                time.sleep(0.01)

    def remove_until_dot(self, text):
        dot_index = text.find('.')
        if dot_index < len(text) - 1 and dot_index != -1:
            return text[dot_index + 1:]
        return text

    def stop_and_destroy_thread(self):
        """
        Signals the transcription thread to stop and waits for it to terminate.
        """
        # Set the stop event to signal the thread to exit
        self.stop_event.set()

        # Wait for the thread to finish execution
        self.trans_thread.join(timeout=3)  # Adjust timeout as needed

        if self.trans_thread.is_alive():
            print("Thread did not terminate within"
                  "the timeout period.")
        else:
            print("Transcription thread has been successfully stopped.")

    def display_translation_info(self, message: dict):

        print("=========================+================================")
        print(f"SPEAKER LANG: {self.speaker_lang}")
        if isinstance(message, tuple):
            try:
                # Assuming message is a tuple of key-value pairs
                message = dict(message)
            except (TypeError, ValueError) as e:
                print(f"[ERROR] Unable to convert tuple to dict: {e}")
                return
        for k, v in message.items():
            if k == "translate":
                print(k.upper(), " :")
                for lang, translated_text in v.items():
                    print(f" - {lang.upper()} - {translated_text}")
            else:
                print(f"{k.upper()} - {v}")

    def send_translations_to_all_listeners(self, translations):
        """
        Build translation message, display it,
        and attempt to broadcast to all listeners.
        """
        message = {
            "id": self.translation_id,
            "start": self.translation_start_time,
            "end": self.translation_end_time,
            "translate": translations,
        }

        self.display_translation_info(message)

        try:
            self.server.listener_manager.send_message_to_all_listeners(
                message=message,
                client_uid=self.client_uid
            )
            self.translation_id += 1
        except Exception as e:
            logging.error('[ERROR SEND TO LISTENERS - LISTENER CONNECTION LOST]')

    def is_rtl(self):
        return self.speaker_lang in ['ar', 'he', 'fa', 'ur', 'ps', 'sd']

    def normalize_string(self, s):
        s = s.lower()
        s = s.translate(str.maketrans('', '', string.punctuation))
        s = ' '.join(s.split())
        return s

    def are_strings_equal(self, str1, str2):
        return self.normalize_string(str1) == self.normalize_string(str2)

    def prepare_translations(self):
        translations = self.translator.get_translations(
                text=self.translation_accumulated_text,
                src_lang=self.speaker_lang,
                tgt_langs=self.all_langs
            )


        translations = translations.get('translate', {})
        translations[self.speaker_lang] = self.translation_accumulated_text
        self.previous_translation_accumulated_text = self.translation_accumulated_text
        self.translation_accumulated_text = ""

        return translations

    def format_segment(self, start: float, end: float, text: str, translate: bool = False) -> dict:
        """
        Formats a transcription segment with precise start and end times, along with the text.
        For RTL languages (ar, he, fa, etc.), accumulates text until translation is done.
        For LTR languages, text is sent immediately (no accumulation).
        If `translate` changes from True to False and we're in RTL mode,
        finishes up accumulated text with a translation call.
        """

        # Prepare output item
        item = {
            "start": f"{start:.3f}",
            "end": f"{end:.3f}",
            "text": text,
        }

        rtl_language = self.is_rtl()

        # (A) Potentially start accumulating text (RTL only)
        #     When `translate` just turned on and wasn't on before.
        if translate and not self.previous_segment_ready:
            self.translation_start_time = item["start"]

        # (B) If `translate` just turned off (finishing a segment) and we had accumulated text
        if (not translate
                and self.previous_segment_ready
                and self.translation_accumulated_text):

            if rtl_language:
                # Check duplicates in RTL scenario
                if not self._is_duplicate_rtl():
                    translation_thread = threading.Thread(target=self.translate_and_send_thread, daemon=True)
                    translation_thread.start()
                else:
                    print(" **** CAUGHT DUPLICATE (RTL) **** ")
                    self.previous_translation_accumulated_text = ""
                    self.translation_accumulated_text = ""

        # (C) If we're currently in translation mode, handle text
        if translate:
            self.translation_end_time = item["end"]

            # (C1) RTL: accumulate text
            if rtl_language:
                combined = text + " " + self.translation_accumulated_text
                self.translation_accumulated_text = combined.strip()

            # (C2) LTR: send immediately
            else:
                if not self.disable_sentence_cutter:
                    processed = self.sa.process_segment(text)
                else:
                    processed = text

                if processed:
                    self.translation_accumulated_text = processed
                    translation_thread = threading.Thread(target=self.translate_and_send_thread, daemon=True)
                    translation_thread.start()

        # Update state for next call
        self.previous_segment_ready = (translate and rtl_language)
        return item

    def _is_duplicate_rtl(self) -> bool:
        """
        Compares previously finalized text with the currently accumulated text,
        returning True if the new text is a prefix of the old text.
        """
        prev_text = self.previous_translation_accumulated_text.lower().strip()
        curr_text = self.translation_accumulated_text.lower().strip()
        return prev_text.startswith(curr_text)


    def update_segments(self, segments, duration):
        """
        Processes the segments from whisper. Appends all the segments to the list
        except for the last segment assuming that it is incomplete.

        Updates the ongoing transcript with transcribed segments, including their start and end times.
        Complete segments are appended to the transcript in chronological order. Incomplete segments
        (assumed to be the last one) are processed to identify repeated content. If the same incomplete
        segment is seen multiple times, it updates the offset and appends the segment to the transcript.
        A threshold is used to detect repeated content and ensure it is only included once in the transcript.
        The timestamp offset is updated based on the duration of processed segments. The method returns the
        last processed segment, allowing it to be sent to the client for real-time updates.

        Args:
            segments(dict) : dictionary of segments as returned by whisper
            duration(float): duration of the current chunk

        Returns:
            dict or None: The last processed segment with its start time, end time, and transcribed text.
                     Returns None if there are no valid segments to process.
        """
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
                self.transcript.append(self.format_segment(start, end, text_, True))
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
                    self.current_out,
                    True
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