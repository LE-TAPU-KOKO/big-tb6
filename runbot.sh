#!/bin/bash
cd "$(dirname "$0")/server" || exit
source .venv/bin/activate
python bot.py -t webrtc --host localhost --port 7860
