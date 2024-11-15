from whisper_live.client import TranscriptionClient
#5.2.174.20:23647
client = TranscriptionClient(
    host ="5.2.174.20",
    port = 23647,
    lang="ru",
    translate=False,
    model="large-v3",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav",  # Only used for microphone input
    ignore_ssl_cert=True
)

client()
