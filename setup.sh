#! /bin/bash

apt-get install portaudio19-dev ffmpeg wget -y
pip install -r ./requirements/server.txt
pip install ctranslate2==4.4.0