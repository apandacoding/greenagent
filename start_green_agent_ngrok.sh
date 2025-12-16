#!/bin/bash
# Quick deployment script using ngrok for testing

echo "=========================================="
echo "Starting Green Agent with ngrok"
echo "=========================================="
echo ""
echo "This will:"
echo "1. Start the AgentBeats controller on port 8101"
echo "2. Start the green agent on port 8001"
echo "3. Expose the controller publicly via ngrok"
echo ""
echo "=========================================="

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed!"
    echo ""
    echo "Install it with:"
    echo "  brew install ngrok"
    echo ""
    echo "Or download from: https://ngrok.com/download"
    exit 1
fi

# Check if venv exists and agentbeats is installed
if [ ! -d "venv" ]; then
    echo "❌ venv not found. Creating one..."
    python3.13 -m venv venv
fi

echo "Activating venv..."
source venv/bin/activate

# Check if agentbeats is installed
if ! python -c "import a2a" 2>/dev/null; then
    echo "❌ agentbeats not installed in venv"
    echo "Installing agentbeats..."
    pip install agentbeats
fi

echo ""
echo "✅ Environment ready!"
echo ""

# Start the controller in the background
echo "Starting AgentBeats controller..."
ROLE=green AGENT_PORT=8001 HOST=0.0.0.0 \
    python backend/agentbeats_controller.py --port 8101 --host 0.0.0.0 &
CONTROLLER_PID=$!

echo "Controller started (PID: $CONTROLLER_PID)"
echo "Waiting for controller to be ready..."
sleep 5

# Check if controller is running
if ! curl -s http://localhost:8101/status > /dev/null; then
    echo "❌ Controller failed to start!"
    echo "Check the logs above for errors"
    kill $CONTROLLER_PID 2>/dev/null
    exit 1
fi

echo "✅ Controller is running!"
echo ""

# Start ngrok
echo "=========================================="
echo "Starting ngrok tunnel..."
echo "=========================================="
echo ""
echo "Your controller will be accessible at the ngrok URL"
echo "Press Ctrl+C to stop everything"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $CONTROLLER_PID 2>/dev/null
    pkill -P $$ 2>/dev/null
    echo "Done!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start ngrok and show the URL
ngrok http 8101 --log=stdout | tee >(
    grep -o 'url=https://[^ ]*' | 
    head -1 | 
    sed 's/url=//' | 
    while read url; do
        echo ""
        echo "=========================================="
        echo "🎉 YOUR PUBLIC CONTROLLER URL:"
        echo "$url"
        echo "=========================================="
        echo ""
        echo "Test it:"
        echo "  curl $url/status"
        echo "  curl $url/agents"
        echo "  curl $url/.well-known/agent-card.json"
        echo ""
        echo "Use this URL in the AgentBeats form!"
        echo "=========================================="
    done
)
