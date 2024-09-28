from whisper_live.client import TranscriptionClient

client = TranscriptionClient(
    "127.0.0.1",
    9090,
    lang="hybrid",
    translate=True,
    model="large-v3",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav"  # Only used for microphone input
)

client()
