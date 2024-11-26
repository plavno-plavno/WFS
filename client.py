from whisper_live.client import TranscriptionClient
#193.69.10.15:50506
client = TranscriptionClient(
    host ="193.69.10.15",
    port = 50506,
    lang="ar",
    translate=False,
    model="large-v3",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav",  # Only used for microphone input
    ignore_ssl_cert=True
)

client()
