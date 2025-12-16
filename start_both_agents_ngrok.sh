#!/bin/bash
# start_both_agents_ngrok.sh - Start both Green and White agents with shared ngrok tunnel
# Uses a reverse proxy to route both agents through one ngrok URL

set -e

echo "=========================================="
echo "Starting Both Agents with Shared ngrok"
echo "=========================================="

# Activate venv if it exists
if [ -d "venv" ]; then
    echo "Activating venv..."
    source venv/bin/activate
fi

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ Error: ngrok is not installed"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Kill any existing processes on these ports
echo "Cleaning up existing processes..."
lsof -ti:8100,8101,8102 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 2

echo ""
echo "Step 1: Starting ngrok tunnel (port 8100)..."
nohup ngrok http 8100 --log=stdout > logs/ngrok_shared.log 2>&1 &
NGROK_PID=$!
echo "✅ ngrok started (PID: $NGROK_PID)"

# Wait for ngrok and get URL
sleep 5
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok[^"]*' | head -n 1)

if [ -z "$NGROK_URL" ]; then
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null)
fi

if [ -z "$NGROK_URL" ]; then
    echo "⚠️  Could not detect ngrok URL"
    NGROK_URL="http://localhost:8100"
else
    echo "✅ ngrok URL: $NGROK_URL"
fi

echo ""
echo "Step 2: Starting Green Agent Controller (port 8101)..."
ROLE=green AGENT_PORT=8001 HOST=0.0.0.0 PUBLIC_URL="$NGROK_URL/green" \
    nohup bash -c "
        cd '$(pwd)'
        if [ -d 'venv' ]; then source venv/bin/activate; fi
        python backend/agentbeats_controller.py --port 8101 --host 0.0.0.0 --public-url '$NGROK_URL/green'
    " > logs/green_controller_shared.log 2>&1 &
GREEN_PID=$!
echo "✅ Green Controller started (PID: $GREEN_PID)"

echo ""
echo "Step 3: Starting White Agent Controller (port 8102)..."
ROLE=white AGENT_PORT=8002 HOST=0.0.0.0 PUBLIC_URL="$NGROK_URL/white" \
    nohup bash -c "
        cd '$(pwd)'
        if [ -d 'venv' ]; then source venv/bin/activate; fi
        python backend/agentbeats_controller.py --port 8102 --host 0.0.0.0 --public-url '$NGROK_URL/white'
    " > logs/white_controller_shared.log 2>&1 &
WHITE_PID=$!
echo "✅ White Controller started (PID: $WHITE_PID)"

# Wait for controllers to be ready
echo ""
echo "Waiting for controllers to be ready..."
sleep 5

echo ""
echo "Step 4: Starting Reverse Proxy (port 8100)..."
nohup python proxy_server.py > logs/proxy.log 2>&1 &
PROXY_PID=$!
echo "✅ Proxy started (PID: $PROXY_PID)"

# Wait for proxy to be ready
sleep 3

echo ""
echo "=========================================="
echo "🎉 All Services Running!"
echo "=========================================="
echo ""
echo "📡 Public URLs (for AgentBeats):"
echo "  Green Agent: $NGROK_URL/green"
echo "  White Agent: $NGROK_URL/white"
echo ""
echo "🖥️  Local URLs:"
echo "  Proxy UI: http://localhost:8100"
echo "  Green Controller: http://localhost:8101"
echo "  White Controller: http://localhost:8102"
echo "  ngrok Dashboard: http://localhost:4040"
echo ""
echo "📋 Test Commands:"
echo "  curl $NGROK_URL/green/status"
echo "  curl $NGROK_URL/white/status"
echo "  curl $NGROK_URL/green/agents"
echo "  curl $NGROK_URL/white/agents"
echo ""
echo "📝 Logs:"
echo "  tail -f logs/proxy.log"
echo "  tail -f logs/green_controller_shared.log"
echo "  tail -f logs/white_controller_shared.log"
echo "  tail -f logs/ngrok_shared.log"
echo ""
echo "=========================================="

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping all services..."
    kill $PROXY_PID 2>/dev/null || true
    kill $GREEN_PID 2>/dev/null || true
    kill $WHITE_PID 2>/dev/null || true
    kill $NGROK_PID 2>/dev/null || true
    pkill -P $GREEN_PID 2>/dev/null || true
    pkill -P $WHITE_PID 2>/dev/null || true
    echo "All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Press Ctrl+C to stop all services"
echo "=========================================="
echo ""
echo "📜 Showing proxy logs..."
echo ""

# Follow proxy logs
tail -f logs/proxy.log
