#!/bin/bash

# Define paths to SSL files and optional passphrase
SSL_CERT_FILE="certificates/fullchain1.pem"
SSL_KEY_FILE="certificates/privkey1.pem"
SSL_PASSPHRASE=""  # Set this to your SSL key passphrase if needed

# Determine the path to python
if [ -x "/opt/conda/bin/python" ]; then
    CMD="/opt/conda/bin/python"
else
    CMD="python"
fi

# Initialize SSL options
SSL_OPTIONS=""

# Check if SSL certificate and key files exist
if [[ -f "$SSL_CERT_FILE" && -f "$SSL_KEY_FILE" ]]; then
    echo "SSL files found. Enabling SSL support."
    SSL_OPTIONS="--ssl_cert_file \"$SSL_CERT_FILE\" --ssl_key_file \"$SSL_KEY_FILE\""

    # Add passphrase if provided
    if [[ -n "$SSL_PASSPHRASE" ]]; then
        SSL_OPTIONS="$SSL_OPTIONS --ssl_passphrase \"$SSL_PASSPHRASE\""
    fi
else
    echo "SSL files not found. Running without SSL support."
fi

# Run the Python server script with appropriate SSL options
eval "$CMD run_server.py --port 9090 --backend faster_whisper -fw 'faster-whisper-large-v3' $SSL_OPTIONS" >> run_server.log 2>&1
