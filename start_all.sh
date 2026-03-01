#!/bin/bash

# BigTB6 - Start all services

echo "🚀 Starting BigTB6 Services..."

# Get the project root
PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"
SERVER_DIR="$PROJECT_ROOT/server"
CLIENT_DIR="$PROJECT_ROOT/client"

# Check if virtual environment exists
if [ ! -d "$SERVER_DIR/.venv" ]; then
    echo "❌ Virtual environment not found at $SERVER_DIR/.venv"
    echo "   Run: cd $SERVER_DIR && python -m venv .venv"
    exit 1
fi

# Function to kill processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."

    # Kill backend API
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "  ✋ Stopped Backend API (PID: $BACKEND_PID)"
    fi

    # Kill WebRTC Bot
    if [ ! -z "$BOT_PID" ]; then
        kill $BOT_PID 2>/dev/null
        echo "  ✋ Stopped WebRTC Bot (PID: $BOT_PID)"
    fi

    echo "✅ All services stopped."
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Activate virtual environment
source "$SERVER_DIR/.venv/Scripts/activate"

# Start Backend API (main.py) on port 8000
echo "📡 Starting Backend API (FastAPI) on port 8000..."
cd "$SERVER_DIR"
python main.py > /tmp/backend_api.log 2>&1 &
BACKEND_PID=$!
echo "   Backend API started (PID: $BACKEND_PID)"

# Wait a moment for API to start
sleep 2

# Start WebRTC Bot (bot.py) on port 7860
echo "🤖 Starting WebRTC Bot (Pipecat) on port 7860..."
python bot.py -t webrtc --host localhost --port 7860 > /tmp/bot.log 2>&1 &
BOT_PID=$!
echo "   WebRTC Bot started (PID: $BOT_PID)"

echo ""
echo "✅ All services started!"
echo ""
echo "📋 Service URLs:"
echo "   Frontend:     http://localhost:3000"
echo "   Backend API:  http://localhost:8000"
echo "   WebRTC Bot:   http://localhost:7860"
echo ""
echo "📝 Logs:"
echo "   Backend API:  tail -f /tmp/backend_api.log"
echo "   WebRTC Bot:   tail -f /tmp/bot.log"
echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# Wait for any process to exit
wait $BACKEND_PID $BOT_PID
cleanup
