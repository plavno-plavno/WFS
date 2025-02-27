from whisper_live.client import TranscriptionClient

client = TranscriptionClient(
    host ="c18136649.plavno.app",
    port = 55375,
    lang="ru",
    translate=False,
    model="large-v3",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav",  # Only used for microphone input
    ignore_ssl_cert=True
)

client()



# Автором этой книги является Антуан де Сент-Экзюпери, но в данном контексте речь идет о книге «Государь» Никколо Макиавелли.