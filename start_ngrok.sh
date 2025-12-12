#!/bin/bash
# Start ngrok tunnel for Green Agent backend

echo "🚀 Starting ngrok tunnel for Green Agent backend..."
echo "📡 Backend should be running on port 8001"
echo ""

# Start ngrok on port 8001
ngrok http 8001

