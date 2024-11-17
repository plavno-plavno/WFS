from whisper_live.client import TranscriptionClient
#172.81.127.5:51722
client = TranscriptionClient(
    host ="172.81.127.5",
    port = 51722,
    lang="ru",
    translate=False,
    model="large-v3",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav",  # Only used for microphone input
    ignore_ssl_cert=True
)

client()
