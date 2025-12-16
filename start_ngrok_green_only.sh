#!/bin/bash
# Start only Green Agent with ngrok (for AgentBeats)
# This is the simplest setup since free ngrok allows only 1 tunnel

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

echo "🚀 Starting Green Agent with Ngrok"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $GREEN_AGENT_PID $NGROK_PID 2>/dev/null || true
    exit
}

trap cleanup INT TERM

# Check if port is available
if lsof -ti:8001 > /dev/null 2>&1; then
    echo "⚠️  Port 8001 is already in use. Killing existing process..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Create logs directory
mkdir -p logs

# Start Green Agent (port 8001)
echo "📡 Starting Green Agent on port 8001..."
cd backend
ENABLE_NGROK=true python api_server.py > ../logs/green_agent.log 2>&1 &
GREEN_AGENT_PID=$!
cd ..
echo "   Green Agent PID: $GREEN_AGENT_PID"

# Wait a bit for server to start
sleep 3

# Check if server is running
if ! kill -0 $GREEN_AGENT_PID 2>/dev/null; then
    echo "❌ Green Agent failed to start"
    echo "   Check logs/green_agent.log for details:"
    tail -20 logs/green_agent.log
    exit 1
fi

echo "✅ Green Agent started"
echo ""

# Start ngrok tunnel
echo "🌐 Starting ngrok tunnel..."
ngrok http 8001 --log=stdout > logs/ngrok.log 2>&1 &
NGROK_PID=$!
sleep 5

# Extract URL from ngrok log
NGROK_URL=""
for i in {1..5}; do
    NGROK_URL=$(grep -o 'https://[a-z0-9-]*\.ngrok-free\.app\|https://[a-z0-9-]*\.ngrok\.io' logs/ngrok.log 2>/dev/null | head -1)
    if [ -n "$NGROK_URL" ]; then
        break
    fi
    sleep 1
done

if [ -n "$NGROK_URL" ]; then
    echo "✅ Ngrok tunnel started!"
    echo "   Public URL: $NGROK_URL"
    echo ""
    echo "📋 Set these environment variables and restart the Green Agent:"
    echo "   export AGENT_URL=$NGROK_URL"
    echo "   export CLOUDRUN_HOST=$(echo $NGROK_URL | sed 's|https://||')"
    echo "   export HTTPS_ENABLED=true"
    echo ""
    echo "   Then restart the Green Agent with these env vars set"
    echo ""
    echo "🎯 AgentBeats Controller URL:"
    echo "   $NGROK_URL/to_agent/YOUR_AGENT_ID"
else
    echo "⚠️  Ngrok URL not found yet"
    echo "   Check logs/ngrok.log for details"
    echo "   You may need to wait a few more seconds"
fi

echo ""
echo "✅ Services started!"
echo ""
echo "Backend Server:"
echo "  - Green Agent: http://localhost:8001"
echo ""
echo "Ngrok Tunnel:"
echo "  - Public URL: $NGROK_URL"
echo ""
echo "Logs:"
echo "  - Green Agent: tail -f logs/green_agent.log"
echo "  - Ngrok: tail -f logs/ngrok.log"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait

