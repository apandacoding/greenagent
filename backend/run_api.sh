#!/bin/bash

# Simple script to run the API server from backend directory

echo "🚀 Starting White Agent API Server..."

# Check if we're in the backend directory
if [ ! -f "api_server.py" ]; then
    echo "❌ Error: Must be run from the backend directory"
    echo "   cd backend && ./run_api.sh"
    exit 1
fi

# Start the server
echo "✅ Starting server on http://localhost:8000"
python api_server.py


