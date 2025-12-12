#!/bin/bash
# Run Green Agent with ngrok tunnel

set -e

echo "🚀 Starting Green Agent with ngrok..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed. Install it with: brew install ngrok"
    exit 1
fi

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "api_server.py" 2>/dev/null || true
pkill -f "ngrok" 2>/dev/null || true
sleep 2

# Start backend
echo -e "${BLUE}📡 Starting backend server...${NC}"
cd "$(dirname "$0")"
source venv/bin/activate
cd backend
ENABLE_NGROK=true python api_server.py > /tmp/green-agent-backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8001/health > /dev/null; then
    echo "❌ Backend failed to start. Check /tmp/green-agent-backend.log"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Backend is running on http://localhost:8001${NC}"

# Start ngrok
echo -e "${BLUE}🌐 Starting ngrok tunnel...${NC}"
ngrok http 8001 --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
echo "Ngrok PID: $NGROK_PID"

# Wait for ngrok to start
sleep 3

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
    echo "⚠️  Could not get ngrok URL. Check ngrok status at http://localhost:4040"
    NGROK_URL="https://your-ngrok-url.ngrok-free.app"
else
    echo -e "${GREEN}✅ Ngrok tunnel: ${NGROK_URL}${NC}"
fi

# Convert HTTP to WebSocket URL
WS_URL=$(echo "$NGROK_URL" | sed 's|https://|wss://|' | sed 's|http://|ws://|')

echo ""
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Backend URL: $NGROK_URL"
echo "  WebSocket URL: $WS_URL"
echo ""
echo -e "${YELLOW}🔧 To start frontend with ngrok:${NC}"
echo "  cd frontend"
echo "  VITE_API_URL=$NGROK_URL VITE_WS_URL=$WS_URL npm run dev"
echo ""
echo -e "${YELLOW}📊 Monitor:${NC}"
echo "  Backend logs: tail -f /tmp/green-agent-backend.log"
echo "  Ngrok dashboard: http://localhost:4040"
echo ""
echo -e "${YELLOW}🛑 To stop:${NC}"
echo "  pkill -f 'api_server.py'"
echo "  pkill -f 'ngrok'"
echo ""

# Keep script running
wait

