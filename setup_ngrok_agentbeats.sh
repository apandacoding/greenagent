#!/bin/bash
# setup_ngrok_agentbeats.sh - Configure ngrok for AgentBeats controller
# This script sets up ngrok to expose your controller publicly

set -e

echo "=========================================="
echo "AgentBeats + ngrok Setup"
echo "=========================================="

# Set ngrok authtoken
NGROK_TOKEN="36rEdd2UeQf9wiIMTcLzZuSFDQI_Fz4swVHo5ba3Lju3NuSx"

echo "Adding ngrok authtoken..."
ngrok config add-authtoken $NGROK_TOKEN

echo ""
echo "✅ ngrok configured successfully!"
echo ""
echo "Next steps:"
echo "1. Start your green agent controller: ./start_agentbeats_green_ngrok.sh"
echo "2. Get the public URL from ngrok"
echo "3. Register on AgentBeats with that URL"
echo ""


