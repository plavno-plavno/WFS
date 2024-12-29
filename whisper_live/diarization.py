import torch
from pyannote.audio import Pipeline


class SpeakerDiarization:
    def __init__(self, use_auth_token=None):
        """
        Initialize the speaker diarization object, load the pre-trained model,
        and move the pipeline to GPU if available.
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.pipeline = self.load_pipeline(use_auth_token)

    def load_pipeline(self, use_auth_token=None):
        """
        Load the pre-trained speaker diarization pipeline.
        """
        try:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=use_auth_token
            )
            pipeline.to(self.device)
            print("Pipeline loaded successfully.")
            return pipeline
        except Exception as e:
            print(f"Error loading the pipeline: {e}")
            exit(1)

    def diarize(self, audio_np, sample_rate=16000):
        """
        Perform speaker diarization on the given audio data.

        :param audio_np: NumPy array of audio data
        :param sample_rate: Sample rate of the audio data (default is 16000)
        :return: List of tuples containing speaker labels and start-end times
        """
        waveform = torch.from_numpy(audio_np).unsqueeze(0).to(
            self.device)  # Convert numpy array to tensor and add batch dimension

        # Perform diarization
        try:
            diarization = self.pipeline({"waveform": waveform, "sample_rate": sample_rate})

            # Process and return the diarization results
            return self.process_diarization(diarization)
        except Exception as e:
            print(f"Error during diarization: {e}")
            return []

    def process_diarization(self, diarization):
        """
        Process diarization results and return the aggregated speaker intervals as an array.
        """

        # Iterate through the diarization results and store intervals by speaker
        for speech_turn, track, label in diarization.itertracks(yield_label=True):
            start_time = speech_turn.start
            end_time = speech_turn.end
            speaker = label




