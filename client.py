from whisper_live.client import TranscriptionClient

client = TranscriptionClient(
    uid = 'tester',
    host = "75.157.149.187",
    port = 44390,
    lang = "ru",
    translate=False,
    model="small",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav"  # Only used for microphone input
)

client()
