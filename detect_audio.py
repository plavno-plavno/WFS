import asyncio
from whisper_live.client import TranscriptionClient


async def transcribe_audio(client_id, audio_file, language):

    try:
        print(f"Initializing client {client_id}...")
        client = TranscriptionClient(
            "localhost",
            9090,
            lang=language,
            translate=True,
            model="small",
            use_vad=False,
            save_output_recording=False,  # Disable saving voice recording
        )
        
        print(f"Client {client_id} is processing {audio_file}...")
        
        # Read audio file
        try:
            with open(audio_file, "rb") as file:
                audio_data = file.read()
                print(f"Audio file '{audio_file}' opened successfully. Size: {len(audio_data)} bytes.")
        except Exception as e:
            print(f"Failed to open audio file {audio_file}: {e}")
            return
        
        # Process transcription
        try:
            print(f"Sending audio file {audio_file} for transcription...")
            transcription = await asyncio.wait_for(client(audio_file), timeout=60)  # Add timeout to prevent hanging
            print(transcription, 'zzzzzz')

            if transcription:
                print(f"Transcription result: {transcription}")
            else:
                print(f"No transcription result for {audio_file}.")
                return  # No transcription, exit early
        except asyncio.TimeoutError:
            print(f"Transcription for {audio_file} took too long and timed out.")
        except Exception as e:
            print(f"Error during transcription process for client {client_id}: {e}")
        
        # Save transcription to an output.srt
        srt_filename = f"client_{client_id}_output.srt"
        try:
            with open(srt_filename, "w") as srt_file:
                srt_file.write("Hello world")  # For testing purposes, write a placeholder
            print(f"Transcription saved to {srt_filename}")
        except Exception as e:
            print(f"Error writing transcription to {srt_filename}: {e}")
        
    except Exception as e:
        print(f"Client {client_id} encountered an error: {e}")

async def main():
    audio_file = "test3.wav"
    tasks = [transcribe_audio(1, audio_file, 'en')]  # Test with a single file for debugging
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
