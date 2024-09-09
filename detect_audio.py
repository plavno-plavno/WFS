import asyncio
from whisper_live.client import TranscriptionClient

async def transcribe_audio(client_id, audio_file, langugage):
    client = TranscriptionClient(
        "localhost",          
        9090,                
        lang=langugage,          
        translate=True,      
        model="small",        
        use_vad=False,       
        save_output_recording=True,                 
        output_recording_filename=f"./client_{client_id}_output.wav"  
    )
    
    print(f"Client {client_id} is transcribing {audio_file}")
    transcription = client(audio_file)
    
    print(f"Client {client_id} transcription result: {transcription}")

async def main():
    audio_file = "./my_voice.wav"
    audio_file2 = "./az_voice.wav"

    my_list = [audio_file, audio_file2]
    
    tasks = []
    count = 0
    for i in my_list:
        count += 1
        tasks.append(transcribe_audio(count, i, 'en'))
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())