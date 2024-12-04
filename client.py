from whisper_live.client import TranscriptionClient
#185.62.108.226:45201
client = TranscriptionClient(
    host ="185.62.108.226",
    port = 45201,
    lang="en",
    translate=False,
    model="large-v3",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav",  # Only used for microphone input
    ignore_ssl_cert=True
)

client()
