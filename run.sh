#!/bin/bash

# Define paths to SSL files and optional passphrase
SSL_CERT_FILE="certificates/fullchain1.pem"
SSL_KEY_FILE="certificates/privkey1.pem"
SSL_PASSPHRASE=""  # Set this to your SSL key passphrase if needed

# Base URL for faster-whisper-large-v3 files
BASE_URL="https://huggingface.co/Systran/faster-whisper-large-v3/resolve/main"
FW_DIR="faster-whisper-large-v3"
FW_FILES=(
    "model.bin"
    "config.json"
    "preprocessor_config.json"
    "tokenizer.json"
    "vocabulary.json"
)

# Function to ensure the directory exists and download missing files
ensure_fw_files() {
    local dir="$1"
    local base_url="$2"
    shift 2
    local files=("$@")

    # Create the directory if it doesn't exist
    if [ ! -d "$dir" ]; then
        echo "Directory $dir not found. Creating and downloading required files."
        mkdir -p "$dir"
    else
        echo "Directory $dir found. Checking for missing files."
    fi

    # Loop through files and download missing ones
    for file_name in "${files[@]}"; do
        if [ ! -f "$dir/$file_name" ]; then
            echo "File $file_name is missing. Downloading..."
            wget -P "$dir" "$base_url/$file_name"
        fi
    done
}

# Call the function to ensure faster-whisper-large-v3 files are available
ensure_fw_files "$FW_DIR" "$BASE_URL" "${FW_FILES[@]}"

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
eval "$CMD run_server.py --port 9090 --backend faster_whisper -fw \"$FW_DIR\" $SSL_OPTIONS"
