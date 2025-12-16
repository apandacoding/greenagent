#!/bin/bash
# start_both_agentbeats.sh - Launch both Green and White agents with AgentBeats controllers
# This script runs both agents in the background

set -e

echo "=========================================="
echo "Starting Both Agents with AgentBeats"
echo "=========================================="

# Create logs directory if it doesn't exist
mkdir -p logs

# Determine which Python to use
PYTHON_CMD="python3.11"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping agents..."
    pkill -P $$ || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Green Agent in background
echo "Starting Green Agent (Port 8001, Controller Port 8101)..."
ROLE=green AGENT_PORT=8001 HOST=0.0.0.0 \
    nohup $PYTHON_CMD backend/agentbeats_controller.py --port 8101 --host 0.0.0.0 \
    > logs/green_controller.log 2>&1 &
GREEN_PID=$!
echo "Green Agent started (PID: $GREEN_PID)"

# Wait a moment for green to initialize
sleep 2

# Start White Agent in background
echo "Starting White Agent (Port 8002, Controller Port 8102)..."
ROLE=white AGENT_PORT=8002 HOST=0.0.0.0 \
    nohup $PYTHON_CMD backend/agentbeats_controller.py --port 8102 --host 0.0.0.0 \
    > logs/white_controller.log 2>&1 &
WHITE_PID=$!
echo "White Agent started (PID: $WHITE_PID)"

echo "=========================================="
echo "Both agents are running!"
echo "=========================================="
echo "Green Agent:"
echo "  - Agent: http://localhost:8001"
echo "  - Controller UI: http://localhost:8101"
echo "  - Logs: logs/green_controller.log"
echo ""
echo "White Agent:"
echo "  - Agent: http://localhost:8002"
echo "  - Controller UI: http://localhost:8102"
echo "  - Logs: logs/white_controller.log"
echo "=========================================="
echo "Press Ctrl+C to stop both agents"
echo ""

# Wait for processes
wait $GREEN_PID $WHITE_PID


