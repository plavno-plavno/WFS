from whisper_live.client import TranscriptionClient
#69.21.145.219:42180
client = TranscriptionClient(
    host ="69.21.145.219",
    port = 42180,
    lang="ar",
    translate=False,
    model="large-v3",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav",  # Only used for microphone input
    ignore_ssl_cert=True
)

client()
