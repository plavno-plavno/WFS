import argparse
import os
import logging
from socketify import App
from whisper_live.server import TranscriptionServer, BackendType
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # Change to DEBUG level

if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p',
                        type=int,
                        default=9090,
                        help="WebSocket port to run the server on.")
    parser.add_argument('--backend', '-b',
                        type=str,
                        default='faster_whisper',
                        help='Backends from ["faster_whisper"]')
    parser.add_argument('--faster_whisper_custom_model_path', '-fw',
                        type=str, default='medium',
                        help="Custom Faster Whisper Model")
    parser.add_argument('--omp_num_threads', '-omp',
                        type=int,
                        default=1,
                        help="Number of threads to use for OpenMP")
    parser.add_argument('--no_single_model', '-nsm',
                        action='store_true',
                        help='Set this if every connection should instantiate its own model. Only relevant for custom model passed using -fw.')
    args = parser.parse_args()

    # Set the environment variable for OpenMP threads
    if "OMP_NUM_THREADS" not in os.environ:
        os.environ["OMP_NUM_THREADS"] = str(args.omp_num_threads)

    logging.debug(f"Starting server with args: {args}")

    try:
        # Initialize the TranscriptionServer
        server = TranscriptionServer()

        # Create the WebSocket server using Socketify
        app = App()

        # WebSocket message handler
        def websocket_message_handler(ws, message, opcode):
            """Handles incoming WebSocket messages."""
            print('=========', id(ws.socket_data_id))
            try:
                #print(f"=====>RUNSERVER: Received message:")# {message}")
                # Convert backend string to BackendType enum
                backend_enum = BackendType(args.backend)

                if isinstance(message, bytes):
                    # Pass the audio data as bytes directly to the transcription server
                    #print("=====>RUNSERVER: rocessing audio data.", id(ws))
                    server.recv_audio(ws, backend=backend_enum, faster_whisper_custom_model_path=args.faster_whisper_custom_model_path, message=message)
                else:
                    # If the message is a JSON string, process it directly
                    #print("=====>RUNSERVER: rocessing JSON message.")
                    options = json.loads(message)  # Parse JSON directly from the message string
                    #print(f"=====>RUNSERVER: Parsed JSON: {options}")
                    server.recv_audio(ws, options, backend=backend_enum, faster_whisper_custom_model_path=args.faster_whisper_custom_model_path)
            except Exception as e:
                logging.error(f"Error processing message: {e}")


        # WebSocket close handler
        def websocket_close_handler(ws, code, message):
            """Handles WebSocket disconnection."""
            # print(f"======>: WebSocket connection closed with code: {code}, message: {message}")
            server.cleanup(ws)

        # Add WebSocket route with handlers for open, message, close events
        app.ws("/*", {
            "open": lambda ws: print("======>New WebSocket connection opened.", id(ws.socket_data_id)),
            "message": websocket_message_handler,  # Handle incoming messages
            "close": websocket_close_handler       # Handle WebSocket close event
        })

        # Start listening on the provided port
        app.listen(args.port)

        # Keep server alive
        #print("======>Running server... Press Ctrl+C to stop.")
        app.run()

    except Exception as e:
        print(f"=====>Unexpected error occurred: {e}")
