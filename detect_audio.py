import asyncio
from whisper_live.client import TranscriptionClient

async def transcribe_audio(client_id, audio_file, language):
    print('start---------=======')
    client = TranscriptionClient(
        "localhost",
        9090,
        lang=language,
        translate=True,
        model="small",
        use_vad=False,
        save_output_recording=True,
        output_recording_filename=f"./client_{client_id}_output.wav"
    )
    
    print(f"Client {client_id} is transcribing {audio_file}")

    # Make sure TranscriptionClient returns the transcription result
    transcription = client(audio_file)  

    print(f"Client {client_id} transcription result: {transcription}")
    print('end----===================')
    return transcription  # Ensure it returns the transcription

async def main():
    audio_file = "media/my_voice_converted.wav"
    audio_file2 = "media/second_short.wav"

    my_list = [audio_file]

    tasks = []
    count = 0
    for i in my_list:
        count += 1
        tasks.append(transcribe_audio(count, i, 'en'))

    # Gather the transcription results
    results = await asyncio.gather(*tasks)

    # Log or handle transcription results
    for idx, result in enumerate(results, 1):
        print(f"Transcription for Client {idx}: {result}")

if __name__ == "__main__":
    asyncio.run(main())
