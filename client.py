from whisper_live.client import TranscriptionClient
#74.80.190.164:10270
client = TranscriptionClient(
    host ="74.80.190.164",
    port = 10270,
    lang="ar",
    translate=False,
    model="large-v3",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav",  # Only used for microphone input
    ignore_ssl_cert=True
)

client()
