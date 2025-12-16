#!/bin/bash
# start_agentbeats_green.sh - Launch Green Agent with AgentBeats controller
# Usage: ./start_agentbeats_green.sh

set -e

# Set environment variables for AgentBeats controller
export ROLE=green
export AGENT_PORT=${AGENT_PORT:-8001}
export HOST=${HOST:-0.0.0.0}

# Controller will listen on a different port and proxy to the agent
export CTRL_PORT=${CTRL_PORT:-8101}

echo "=========================================="
echo "Starting Green Agent with AgentBeats Controller"
echo "=========================================="
echo "Agent Role: $ROLE"
echo "Agent will listen on: $HOST:$AGENT_PORT"
echo "Controller will listen on: 0.0.0.0:$CTRL_PORT"
echo "Run script: ./run_green.sh"
echo "=========================================="

# Navigate to project root
cd "$(dirname "$0")"

# Check Python version
PYTHON_CMD="python3.11"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Start the custom AgentBeats controller
# The controller will:
# 1. Run ./run_green.sh to start the agent
# 2. Expose management API on CTRL_PORT
# 3. Provide a management UI
$PYTHON_CMD backend/agentbeats_controller.py --port $CTRL_PORT --host 0.0.0.0


