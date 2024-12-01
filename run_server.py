import argparse
import os
import logging

logging.basicConfig(level=logging.ERROR)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p',
                        type=int,
                        default=9090,
                        help="Websocket port to run the server on.")
    parser.add_argument('--backend', '-b',
                        type=str,
                        default='faster_whisper',
                        help='Backends from ["faster_whisper"]')
    parser.add_argument('--faster_whisper_custom_model_path', '-fw',
                        type=str, default=None,
                        help="Custom Faster Whisper Model")
    parser.add_argument('--no_single_model', '-nsm',
                        action='store_true',
                        help='Set this if every connection should instantiate its own model. Only relevant for custom model passed using -fw.')
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

    args = parser.parse_args()

    from whisper_live.server import TranscriptionServer

    server = TranscriptionServer()

    # Prepare SSL parameters only if SSL files are provided
    ssl_key_file = args.ssl_key_file if args.ssl_key_file else None
    ssl_cert_file = args.ssl_cert_file if args.ssl_cert_file else None
    ssl_passphrase = args.ssl_passphrase if args.ssl_passphrase else None

    server.run(
        "0.0.0.0",
        port=args.port,
        backend=args.backend,
        faster_whisper_custom_model_path=args.faster_whisper_custom_model_path,
        ssl_key_file=ssl_key_file,
        ssl_cert_file=ssl_cert_file,
        ssl_passphrase=ssl_passphrase  # Include this line if passphrase is also needed
    )
