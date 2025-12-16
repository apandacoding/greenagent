#!/bin/bash
# Start ngrok tunnel for White Agent (port 8002)
# This will expose the agent with a public HTTPS URL

echo "🌐 Starting ngrok tunnel for White Agent (port 8002)..."
echo "   Make sure White Agent is running on port 8002"
echo ""

# Start ngrok and capture the URL
ngrok_url=$(ngrok http 8002 --log=stdout 2>&1 | grep -o 'https://[a-z0-9-]*\.ngrok-free\.app\|https://[a-z0-9-]*\.ngrok\.io' | head -1)

if [ -z "$ngrok_url" ]; then
    echo "❌ Failed to get ngrok URL. Make sure ngrok is installed and authenticated."
    echo "   Install: brew install ngrok/ngrok/ngrok"
    echo "   Auth: ngrok config add-authtoken YOUR_TOKEN"
    exit 1
fi

echo "✅ Ngrok tunnel started!"
echo "   Public URL: $ngrok_url"
echo ""
echo "📋 Set these environment variables before starting your agent:"
echo "   export AGENT_URL=$ngrok_url"
echo "   export CLOUDRUN_HOST=$(echo $ngrok_url | sed 's|https://||')"
echo "   export HTTPS_ENABLED=true"
echo ""
echo "Press Ctrl+C to stop ngrok"

# Keep ngrok running
ngrok http 8002

