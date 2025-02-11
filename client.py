from whisper_live.client import TranscriptionClient

client = TranscriptionClient(
    host ="142.115.158.140",
    port = 42779,
    lang="en",
    translate=False,
    model="large-v3",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav",  # Only used for microphone input
    ignore_ssl_cert=True
)

client()
