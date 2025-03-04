import argparse
import logging
import asyncio
from aiohttp import web

logging.basicConfig(level=logging.INFO)


async def check_availability(request: web.Request) -> web.Response:
    """
    Simple handler that returns a JSON response to indicate availability.
    It also shows how you can access the TranscriptionServer instance
    and return the number of connected clients in JSON.
    """
    transcription_server = request.app["transcription_server"]
    client_number = transcription_server.speaker_manager.get_client_count()

    # Return a JSON response instead of plain text
    return web.json_response({
        "clients_number": client_number
    })

async def start_http_server(host: str, port: int, transcription_server) -> None:
    """
    Start an aiohttp-based HTTP server with a single route: /checkAvailability
    and store the TranscriptionServer instance so the route can access it.
    """
    app = web.Application()

    # Store the transcription_server instance on the app object
    app["transcription_server"] = transcription_server

    # Register our route
    app.router.add_get('/check', check_availability)

    # Set up the web server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logging.info(f"HTTP server running on http://{host}:{port}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p',
                        type=int,
                        default=9090,
                        help="Websocket port to run the TranscriptionServer on.")
    parser.add_argument('--backend', '-b',
                        type=str,
                        default='faster_whisper',
                        help='Backends from ["faster_whisper"]')
    parser.add_argument('--faster_whisper_custom_model_path', '-fw',
                        type=str,
                        default=None,
                        help="Custom Faster Whisper Model")
    parser.add_argument('--no_single_model', '-nsm',
                        action='store_true',
                        help='Set this if every connection should instantiate its own model. \
                              Only relevant for custom model passed using -fw.')
    parser.add_argument('--ssl_cert_file', '-scf',
                        type=str,
                        default=None,
                        help="Path to the SSL certificate file.")
    parser.add_argument('--ssl_key_file', '-skf',
                        type=str,
                        default=None,
                        help="Path to the SSL key file.")
    parser.add_argument('--ssl_passphrase', '-sp',
                        type=str,
                        default=None,
                        help="Optional passphrase for the SSL key.")
    parser.add_argument('--http_port', '-hp',
                        type=int,
                        default=8080,
                        help="Port to run the HTTP server on for /checkAvailability, etc.")

    args = parser.parse_args()

    from whisper_live.server import TranscriptionServer

    # Initialize your TranscriptionServer instance
    server = TranscriptionServer()

    # Prepare SSL parameters only if SSL files are provided
    ssl_key_file = args.ssl_key_file if args.ssl_key_file else None
    ssl_cert_file = args.ssl_cert_file if args.ssl_cert_file else None
    ssl_passphrase = args.ssl_passphrase if args.ssl_passphrase else None

    # Retrieve the current running loop
    loop = asyncio.get_running_loop()

    # 1) Start the HTTP server (in the background) for checkAvailability
    #    Pass the 'server' instance so the route can access it.
    asyncio.create_task(start_http_server("0.0.0.0", args.http_port, server))

    # 2) Run the TranscriptionServer in a separate thread via run_in_executor
    await loop.run_in_executor(
        None,  # default ThreadPoolExecutor
        server.run,  # the function
        "0.0.0.0",
        args.port,
        args.backend,
        args.faster_whisper_custom_model_path,
        ssl_cert_file,
        ssl_key_file,
        ssl_passphrase,
        loop
    )


if __name__ == "__main__":
    asyncio.run(main())
