import asyncio
from whisper_live.server import TranscriptionServer

def main():
    server = TranscriptionServer()
    asyncio.run(server.start_server(
        host="localhost",
        port=9090,
        backend="FASTER_WHISPER",
        faster_whisper_custom_model_path=None,
        single_model=False
    ))

if __name__ == "__main__":
    main()
