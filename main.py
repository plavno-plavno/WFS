import uuid
from whisper_live.client import TranscriptionClient

#
# from huggingface_hub import snapshot_download
#
# repo_id = "deepdml/faster-whisper-large-v3-turbo-ct2"
# local_dir = "faster-whisper-large-v3-turbo-ct2"
# snapshot_download(repo_id=repo_id, local_dir=local_dir, repo_type="model")

client = TranscriptionClient(
    str(uuid.uuid4()),
    "127.0.0.1",
    9090,
    lang="en",
    translate=True,
    model="small",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    output_recording_filename="./output_recording.wav"  # Only used for microphone input
)

client()

# from huggingface_hub import snapshot_download
#
# repo_id = "deepdml/faster-whisper-large-v3-turbo-ct2"
# local_dir = "faster-whisper-large-v3-turbo-ct2"
# snapshot_download(repo_id=repo_id, local_dir=local_dir, repo_type="model")
#

# from faster_whisper import WhisperModel
#
# model = WhisperModel("faster-whisper-large-v3-turbo-ct2")
# segments, info = model.transcribe("audio.mp3")
# for segment in segments:
#     print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))


# client = TranscriptionClient(
#     str(uuid.uuid4()),
#     "85.165.201.219",
#     44071,
#     lang=["en", "ru", "de"],
#     translate=True,
#     model="large-v3",
#     use_vad=True,
#     save_output_recording=False,  # Only used for microphone input, False by Default
#     output_recording_filename="./output_recording.wav"  # Only used for microphone input
# )
#
# client()172.81.127.6:42367

# client = TranscriptionClient(
#     str(uuid.uuid4()),
#     "77.48.24.153",
#     40233,
#     lang="ru",
#     translate=True,
#     model="large-v3",
#     use_vad=True,
#     save_output_recording=True,  # Only used for microphone input, False by Default
#     output_recording_filename="./output_recording.wav"  # Only used for microphone input
# )

# client()