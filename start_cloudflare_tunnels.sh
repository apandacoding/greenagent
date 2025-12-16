#!/bin/bash
# Start Cloudflare Tunnels for both White Agent and Green Agent

set -e

CONFIG_FILE="cloudflare-config.yml"
CREDENTIALS_DIR=".cloudflared"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuration file not found: $CONFIG_FILE"
    echo "   Run ./setup_cloudflare_tunnels.sh first"
    exit 1
fi

# Check if credentials exist
if [ ! -d "$CREDENTIALS_DIR" ]; then
    echo "❌ Credentials directory not found: $CREDENTIALS_DIR"
    echo "   Run ./setup_cloudflare_tunnels.sh first"
    exit 1
fi

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared is not installed"
    exit 1
fi

echo "🚀 Starting Cloudflare Tunnel..."
echo "   Config: $CONFIG_FILE"
echo "   Make sure both backend servers are running:"
echo "   - White Agent: port 8002"
echo "   - Green Agent: port 8001"
echo ""

# Start the tunnel (runs in foreground by default)
# To run in background, you can use: nohup cloudflared tunnel run green-agent-tunnel &
cloudflared tunnel --config "$CONFIG_FILE" run green-agent-tunnel

