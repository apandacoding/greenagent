#!/bin/bash
# Start both backend servers and Cloudflare tunnels

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please create it first."
    exit 1
fi

# Activate venv
source venv/bin/activate

echo "🚀 Starting Backend Servers and Cloudflare Tunnels"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $WHITE_AGENT_PID $GREEN_AGENT_PID $CLOUDFLARE_PID 2>/dev/null || true
    exit
}

trap cleanup INT TERM

# Create logs directory
mkdir -p logs

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
sleep 2

# Check if servers are running
if ! kill -0 $WHITE_AGENT_PID 2>/dev/null; then
    echo "❌ White Agent failed to start"
    exit 1
fi

if ! kill -0 $GREEN_AGENT_PID 2>/dev/null; then
    echo "❌ Green Agent failed to start"
    exit 1
fi

echo "✅ Both backend servers started"
echo ""

# Start Cloudflare tunnel
echo "🌐 Starting Cloudflare Tunnel..."
mkdir -p logs
cloudflared tunnel --config cloudflare-config.yml run green-agent-tunnel > logs/cloudflare.log 2>&1 &
CLOUDFLARE_PID=$!
echo "   Cloudflare Tunnel PID: $CLOUDFLARE_PID"
echo ""

echo "✅ All services started!"
echo ""
echo "Backend Servers:"
echo "  - White Agent: http://localhost:8002"
echo "  - Green Agent: http://localhost:8001"
echo ""
echo "Cloudflare Tunnels:"
echo "  - Check logs/cloudflare.log for tunnel URLs"
echo "  - Or check your Cloudflare dashboard"
echo ""
echo "Logs:"
echo "  - White Agent: tail -f logs/white_agent.log"
echo "  - Green Agent: tail -f logs/green_agent.log"
echo "  - Cloudflare: tail -f logs/cloudflare.log"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait

