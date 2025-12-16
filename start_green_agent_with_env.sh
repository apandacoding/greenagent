#!/bin/bash
# Start Green Agent with proper environment variables for AgentBeats

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

# Get ngrok URL (assuming it's running)
# IMPORTANT: Update these values or set them as environment variables before running
NGROK_URL="${AGENT_URL:-https://rangy-heike-presentively.ngrok-free.dev}"
AGENT_ID="${AGENT_ID:-d15325e7-f068-4b47-a899-d66cb8b1e9f1}"

echo "🚀 Starting Green Agent for AgentBeats"
echo ""
echo "📋 Environment variables:"
echo "   AGENT_URL=$NGROK_URL"
echo "   AGENT_ID=$AGENT_ID"
echo "   HTTPS_ENABLED=true"
echo "   ENABLE_NGROK=true"
echo ""

# Set environment variables
export AGENT_URL="$NGROK_URL"
export AGENT_ID="$AGENT_ID"
export HTTPS_ENABLED=true
export ENABLE_NGROK=true

# Check if port is available
if lsof -ti:8001 > /dev/null 2>&1; then
    echo "⚠️  Port 8001 is already in use. Killing existing process..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

echo "📡 Starting Green Agent on port 8001..."
cd backend
python api_server.py

