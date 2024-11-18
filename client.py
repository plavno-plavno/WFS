from whisper_live.client import TranscriptionClient
#83.26.78.146:41074
client = TranscriptionClient(
    host ="83.26.78.146",
    port = 41074,
    lang="ru",
    translate=False,
    model="large-v3",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav",  # Only used for microphone input
    ignore_ssl_cert=True
)

client()
