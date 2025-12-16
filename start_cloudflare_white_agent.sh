#!/bin/bash
# Start temporary Cloudflare tunnel for White Agent (port 8002)
# Tunnel lasts for several hours

echo "🌐 Starting Cloudflare tunnel for White Agent (port 8002)..."
echo "   Make sure White Agent is running on port 8002"
echo ""

cloudflared tunnel --url http://localhost:8002

