#!/bin/bash
# Start frontend with ngrok backend URL

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
    echo "❌ Could not get ngrok URL. Is ngrok running?"
    echo "   Start ngrok with: ngrok http 8001"
    exit 1
fi

# Convert to WebSocket URL (https -> wss)
WS_URL=$(echo "$NGROK_URL" | sed 's|https://|wss://|' | sed 's|http://|ws://|')

echo "🚀 Starting frontend with ngrok backend..."
echo "   API URL: $NGROK_URL"
echo "   WebSocket URL: $WS_URL"
echo ""

cd "$(dirname "$0")/frontend"

VITE_API_URL="$NGROK_URL" \
VITE_WS_URL="$WS_URL" \
npm run dev

