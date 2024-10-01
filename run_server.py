import argparse
import os


if __name__ == "__main__":
    from whisper_live.server import DEF_LANGS
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
    parser.add_argument('--langs', '-l',
                        type=str,
                        nargs='+',
                        default=DEF_LANGS,
                        help='List of languages to support (e.g., ["en", "ar"]).')

    args = parser.parse_args()


    from whisper_live.server import TranscriptionServer
    server = TranscriptionServer()
    server.run(
        "0.0.0.0",
        port=args.port,
        backend=args.backend,
        faster_whisper_custom_model_path=args.faster_whisper_custom_model_path,
        single_model=not args.no_single_model,
        langs=args.langs
    )
