#!/bin/bash

# Install necessary system packages
apt-get install portaudio19-dev ffmpeg wget -y
apt-get install cmake libboost-all-dev

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

MADLAD_BASE_URL="https://huggingface.co/santhosh/madlad400-3b-ct2/resolve/main"
MADLAD_DIR="madlad400-3b"
MADLAD_FILES=(
    "model.bin"
    "config.json"
    "shared_vocabulary.json"
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
ensure_fw_files "$MADLAD_DIR" "$MADLAD_BASE_URL" "${MADLAD_FILES[@]}"

# Determine the path to pip
if [ -x "/opt/conda/bin/pip" ]; then
    PIP_CMD="/opt/conda/bin/pip"
else
    PIP_CMD="pip"
fi

# Install Python packages
$PIP_CMD install -r ./requirements/server.txt
$PIP_CMD install ctranslate2==4.4.0