#!/bin/bash
# start_agentbeats_white_ngrok.sh - Start White Agent controller with ngrok tunnel
# This exposes the controller publicly via ngrok for AgentBeats registration

set -e

# Set environment variables for AgentBeats controller
export ROLE=white
export AGENT_PORT=${AGENT_PORT:-8002}
export HOST=${HOST:-0.0.0.0}
export CTRL_PORT=${CTRL_PORT:-8102}

echo "=========================================="
echo "Starting White Agent with ngrok Tunnel"
echo "=========================================="
echo "Agent Role: $ROLE"
echo "Agent Port: $AGENT_PORT"
echo "Controller Port: $CTRL_PORT"
echo "=========================================="

# Activate venv if it exists
if [ -d "venv" ]; then
    echo "Activating venv..."
    source venv/bin/activate
fi

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ Error: ngrok is not installed"
    echo "Install it from: https://ngrok.com/download"
    exit 1
fi

# Check if controller port is available
if lsof -Pi :$CTRL_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Warning: Port $CTRL_PORT is already in use"
    echo "Kill the process? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        lsof -ti:$CTRL_PORT | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        exit 1
    fi
fi

# Create logs directory
mkdir -p logs

echo ""
echo "Starting ngrok first to get public URL..."
# Start ngrok in background
nohup ngrok http $CTRL_PORT --log=stdout > logs/ngrok_white.log 2>&1 &
NGROK_PID=$!
echo "✅ ngrok started (PID: $NGROK_PID)"

# Wait for ngrok to start and get URL
echo "Waiting for ngrok to be ready..."
sleep 5

# Get ngrok public URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok[^"]*' | head -n 1)

if [ -z "$NGROK_URL" ]; then
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null)
fi

if [ -z "$NGROK_URL" ]; then
    echo "⚠️  Warning: Could not detect ngrok URL"
    NGROK_URL=""
else
    echo "✅ ngrok URL detected: $NGROK_URL"
fi

echo ""
echo "Starting controller in background..."
# Start controller in background with public URL
ROLE=white AGENT_PORT=$AGENT_PORT HOST=$HOST PUBLIC_URL=$NGROK_URL \
    nohup bash -c "
        cd '$(pwd)'
        if [ -d 'venv' ]; then source venv/bin/activate; fi
        python backend/agentbeats_controller.py --port $CTRL_PORT --host 0.0.0.0 --public-url '$NGROK_URL'
    " > logs/white_controller_ngrok.log 2>&1 &

CONTROLLER_PID=$!
echo "✅ Controller started (PID: $CONTROLLER_PID) with public URL"

# Wait for controller to start
echo "Waiting for controller to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:$CTRL_PORT/status > /dev/null 2>&1; then
        echo "✅ Controller is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Controller failed to start. Check logs/white_controller_ngrok.log"
        kill $CONTROLLER_PID 2>/dev/null || true
        kill $NGROK_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

echo ""
echo "=========================================="
echo "🎉 AgentBeats Controller is Live!"
echo "=========================================="

if [ -z "$NGROK_URL" ]; then
    echo "⚠️  Could not auto-detect ngrok URL"
    echo "Visit http://localhost:4040 to see your ngrok dashboard"
else
    echo "🌐 Public Controller URL: $NGROK_URL"
    echo ""
    echo "📋 Use this URL to register on AgentBeats:"
    echo "   Controller URL: $NGROK_URL"
fi

echo ""
echo "Local URLs:"
echo "  - Controller UI: http://localhost:$CTRL_PORT"
echo "  - Controller Status: http://localhost:$CTRL_PORT/status"
echo "  - ngrok Dashboard: http://localhost:4040"
echo ""
echo "Logs:"
echo "  - Controller: tail -f logs/white_controller_ngrok.log"
echo "  - ngrok: tail -f logs/ngrok_white.log"
echo ""
echo "=========================================="
echo "Test Your Setup:"
echo "=========================================="
echo ""
echo "1. Local test:"
echo "   curl http://localhost:$CTRL_PORT/status"
echo ""
if [ -n "$NGROK_URL" ]; then
    echo "2. Public test:"
    echo "   curl $NGROK_URL/status"
    echo ""
    echo "3. Agent card test:"
    echo "   curl $NGROK_URL/agents"
fi
echo ""
echo "Press Ctrl+C to stop (will kill both controller and ngrok)"
echo "=========================================="
echo ""
echo "📜 Showing controller logs (Ctrl+C to stop)..."
echo "=========================================="
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $CONTROLLER_PID 2>/dev/null || true
    kill $NGROK_PID 2>/dev/null || true
    # Also kill any child processes
    pkill -P $CONTROLLER_PID 2>/dev/null || true
    echo "Services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Show logs in real-time
tail -f logs/white_controller_ngrok.log
