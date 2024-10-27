#!/bin/bash

# Install necessary system packages
apt-get install portaudio19-dev ffmpeg wget -y

# Determine the path to pip
if [ -x "/opt/conda/bin/pip" ]; then
    PIP_CMD="/opt/conda/bin/pip"
else
    PIP_CMD="pip"
fi

# Install Python packages
$PIP_CMD install -r ./requirements/server.txt
$PIP_CMD install ctranslate2==4.4.0