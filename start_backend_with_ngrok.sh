#!/bin/bash
# Start both backend servers and ngrok tunnels with proper environment variables

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please create it first."
    exit 1
fi

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed"
    echo ""
    echo "Install it with:"
    echo "  macOS: brew install ngrok/ngrok/ngrok"
    echo "  Or download from: https://ngrok.com/download"
    echo ""
    echo "Then authenticate:"
    echo "  ngrok config add-authtoken YOUR_TOKEN"
    exit 1
fi

# Activate venv
source venv/bin/activate

echo "🚀 Starting Backend Servers and Ngrok Tunnels"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $WHITE_AGENT_PID $GREEN_AGENT_PID $NGROK_WHITE_PID $NGROK_GREEN_PID 2>/dev/null || true
    exit
}

trap cleanup INT TERM

# Create logs directory
mkdir -p logs

# Check if ports are available
if lsof -ti:8002 > /dev/null 2>&1; then
    echo "⚠️  Port 8002 is already in use. Killing existing process..."
    lsof -ti:8002 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

if lsof -ti:8001 > /dev/null 2>&1; then
    echo "⚠️  Port 8001 is already in use. Killing existing process..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Start White Agent (port 8002)
echo "📡 Starting White Agent on port 8002..."
cd backend
ENABLE_NGROK=true PORT=8002 python white_agent_server.py > ../logs/white_agent.log 2>&1 &
WHITE_AGENT_PID=$!
cd ..
echo "   White Agent PID: $WHITE_AGENT_PID"

# Start Green Agent (port 8001)
echo "📡 Starting Green Agent on port 8001..."
cd backend
ENABLE_NGROK=true python api_server.py > ../logs/green_agent.log 2>&1 &
GREEN_AGENT_PID=$!
cd ..
echo "   Green Agent PID: $GREEN_AGENT_PID"

# Wait a bit for servers to start
sleep 3

# Check if servers are running
if ! kill -0 $WHITE_AGENT_PID 2>/dev/null; then
    echo "❌ White Agent failed to start"
    echo "   Check logs/white_agent.log for details:"
    tail -20 logs/white_agent.log
    exit 1
fi

if ! kill -0 $GREEN_AGENT_PID 2>/dev/null; then
    echo "❌ Green Agent failed to start"
    echo "   Check logs/green_agent.log for details:"
    tail -20 logs/green_agent.log
    exit 1
fi

echo "✅ Both backend servers started"
echo ""

# Start ngrok tunnel (free tier allows only 1 session, so we'll use it for Green Agent)
echo "🌐 Starting ngrok tunnel for Green Agent..."
echo "   (Free ngrok accounts are limited to 1 simultaneous session)"
echo "   (Only Green Agent will be exposed - this is what AgentBeats needs)"
echo ""

# Start ngrok for Green Agent in background  
ngrok http 8001 --log=stdout > logs/ngrok_green.log 2>&1 &
NGROK_GREEN_PID=$!
sleep 5

# Extract URL from ngrok log (try multiple times as ngrok may take a moment)
GREEN_URL=""
for i in {1..5}; do
    GREEN_URL=$(grep -o 'https://[a-z0-9-]*\.ngrok-free\.app\|https://[a-z0-9-]*\.ngrok\.io' logs/ngrok_green.log 2>/dev/null | head -1)
    if [ -n "$GREEN_URL" ]; then
        break
    fi
    sleep 1
done

if [ -n "$GREEN_URL" ]; then
    echo "✅ Green Agent ngrok URL: $GREEN_URL"
    echo ""
    echo "📋 Environment variables for AgentBeats:"
    echo "   export AGENT_URL=$GREEN_URL"
    echo "   export CLOUDRUN_HOST=$(echo $GREEN_URL | sed 's|https://||')"
    echo "   export HTTPS_ENABLED=true"
    echo ""
    echo "💡 To set these and restart the Green Agent:"
    echo "   export AGENT_URL=$GREEN_URL"
    echo "   export CLOUDRUN_HOST=$(echo $GREEN_URL | sed 's|https://||')"
    echo "   export HTTPS_ENABLED=true"
    echo "   # Then restart the Green Agent with these env vars"
else
    echo "⚠️  Green Agent ngrok URL not found yet"
    echo "   Check logs/ngrok_green.log for details"
    echo "   You may need to wait a few more seconds"
    echo ""
    echo "   To check manually:"
    echo "   tail -f logs/ngrok_green.log"
fi

echo ""
echo "ℹ️  Note: White Agent is running locally on port 8002 but not exposed via ngrok"
echo "   (Free ngrok tier allows only 1 tunnel)"

echo ""
echo "✅ All services started!"
echo ""
echo "Backend Servers:"
echo "  - White Agent: http://localhost:8002"
echo "  - Green Agent: http://localhost:8001"
echo ""
echo "Ngrok Tunnels:"
echo "  - White Agent: $WHITE_URL"
echo "  - Green Agent: $GREEN_URL"
echo ""
echo "Logs:"
echo "  - White Agent: tail -f logs/white_agent.log"
echo "  - Green Agent: tail -f logs/green_agent.log"
echo "  - Ngrok White: tail -f logs/ngrok_white.log"
echo "  - Ngrok Green: tail -f logs/ngrok_green.log"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait

