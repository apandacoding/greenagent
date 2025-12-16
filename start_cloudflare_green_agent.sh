#!/bin/bash
# Start temporary Cloudflare tunnel for Green Agent (port 8001)
# Tunnel lasts for several hours

echo "🌐 Starting Cloudflare tunnel for Green Agent (port 8001)..."
echo "   Make sure Green Agent is running on port 8001"
echo ""

cloudflared tunnel --url http://localhost:8001

