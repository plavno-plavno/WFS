from whisper_live.client import TranscriptionClient

client = TranscriptionClient(
    "127.0.0.1",
    9090,
    lang="en",
    translate=True,
    model="large-v3",
    use_vad=False,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav"  # Only used for microphone input
)

client()
