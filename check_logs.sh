#!/bin/bash
# Quick script to restart backend with visible logs

echo "🛑 Stopping current backend..."
killall -9 uvicorn 2>/dev/null
sleep 1

echo "🚀 Starting backend with live logs..."
echo "   (Press Ctrl+C to stop)"
echo ""

cd /Users/aryanpanda/green-agent
source venv/bin/activate
cd backend

# Start with visible logs
python -m uvicorn api_server:app --host 127.0.0.1 --port 8001 --reload --log-level info







