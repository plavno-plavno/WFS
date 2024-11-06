from whisper_live.client import TranscriptionClient
#213.91.182.97:40223
client = TranscriptionClient(
    host ="213.91.182.97",
    port = 40223,
    lang="ru",
    translate=False,
    model="large-v3",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav",  # Only used for microphone input
    ignore_ssl_cert=True
)

client()
