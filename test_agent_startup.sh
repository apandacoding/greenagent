#!/bin/bash
# Test script to manually run the agent and see errors

echo "Testing agent startup..."
echo "========================"

cd "$(dirname "$0")"

export ROLE=green
export HOST=0.0.0.0
export AGENT_PORT=8001

echo "Environment:"
echo "  ROLE=$ROLE"
echo "  HOST=$HOST"
echo "  AGENT_PORT=$AGENT_PORT"
echo ""
echo "Running: python3.11 backend/a2a_main.py run"
echo "========================"
echo ""

# Run the agent directly to see errors
cd backend
python3.11 a2a_main.py run


