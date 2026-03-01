#!/bin/bash
set -e

echo "🚀 Starting BigTB6 Backend Services..."

# Start FastAPI server (main.py) in background
echo "📡 Starting FastAPI server on port 8000..."
python main.py &

# Wait for API to start
sleep 3

# Start WebRTC bot (bot.py)
echo "🤖 Starting WebRTC bot on port 7860..."
exec python bot.py -t webrtc --host 0.0.0.0 --port 7860
