#!/bin/bash
# run_white.sh - Startup script for White Agent with AgentBeats controller
# This script is called by the AgentBeats controller to start the white agent
# The controller will set HOST and AGENT_PORT environment variables

# Set the role for this agent
export ROLE=white

# Change to backend directory
cd "$(dirname "$0")/backend"

# Find the correct Python with dependencies installed
# Try python3.13 (venv) first, then python3.11
if command -v python3.13 &> /dev/null && python3.13 -c "import a2a" 2>/dev/null; then
    PYTHON_CMD="python3.13"
elif command -v python3.11 &> /dev/null && python3.11 -c "import a2a" 2>/dev/null; then
    PYTHON_CMD="python3.11"
elif python -c "import a2a" 2>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Cannot find Python with agentbeats/a2a module installed"
    echo "Please run: pip install agentbeats"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"

# Start the agent using a2a_main.py
# HOST and AGENT_PORT are already set by AgentBeats controller
$PYTHON_CMD a2a_main.py run


