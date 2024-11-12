from whisper_live.client import TranscriptionClient
#69.21.145.219:44934
client = TranscriptionClient(
    host ="69.21.145.219",
    port = 44934,
    lang="en",
    translate=True,
    model="large-v3",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav",  # Only used for microphone input
    ignore_ssl_cert=True
)

client()
