#!/bin/bash
# check_all_services.sh - Comprehensive health check for all services

echo "=========================================="
echo "🔍 AgentBeats Services Health Check"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local url=$2
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name${NC} - $url"
        return 0
    else
        echo -e "${RED}❌ $name${NC} - $url"
        return 1
    fi
}

check_json() {
    local name=$1
    local url=$2
    
    response=$(curl -s "$url")
    if echo "$response" | jq . > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name${NC}"
        echo "   $url"
        echo "   Response: $(echo $response | jq -c .)"
    else
        echo -e "${RED}❌ $name${NC}"
        echo "   $url"
        echo "   Response: $response"
    fi
}

echo "1️⃣  Checking Local Services"
echo "----------------------------------------"
check_service "Proxy Server (8100)" "http://localhost:8100"
check_service "Green Controller (8101)" "http://localhost:8101/status"
check_service "White Controller (8102)" "http://localhost:8102/status"
check_service "Green Agent (8001)" "http://localhost:8001/.well-known/agent-card.json"
check_service "White Agent (8002)" "http://localhost:8002/.well-known/agent-card.json"

echo ""
echo "2️⃣  Checking Controllers"
echo "----------------------------------------"
check_json "Green Controller Status" "http://localhost:8101/status"
check_json "White Controller Status" "http://localhost:8102/status"
check_json "Green Controller Agents" "http://localhost:8101/agents"
check_json "White Controller Agents" "http://localhost:8102/agents"

echo ""
echo "3️⃣  Checking ngrok Tunnel"
echo "----------------------------------------"
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null)
    
    if [ -n "$NGROK_URL" ]; then
        echo -e "${GREEN}✅ ngrok Running${NC}"
        echo "   Public URL: $NGROK_URL"
        echo "   Dashboard: http://localhost:4040"
        
        echo ""
        echo "4️⃣  Checking Public URLs"
        echo "----------------------------------------"
        check_service "Proxy Root (Public)" "$NGROK_URL"
        check_json "Green Status (Public)" "$NGROK_URL/green/status"
        check_json "White Status (Public)" "$NGROK_URL/white/status"
        check_json "Green Agents (Public)" "$NGROK_URL/green/agents"
        check_json "White Agents (Public)" "$NGROK_URL/white/agents"
        
        echo ""
        echo "5️⃣  Checking Agent Cards (Public)"
        echo "----------------------------------------"
        check_service "Green Agent Card (Root)" "$NGROK_URL/green/.well-known/agent-card.json"
        
        # Get agent ID from agents endpoint
        GREEN_AGENT_ID=$(curl -s "$NGROK_URL/green/agents" | python3 -c "import sys, json; data=json.load(sys.stdin); print(list(data.keys())[0] if data else '')" 2>/dev/null)
        WHITE_AGENT_ID=$(curl -s "$NGROK_URL/white/agents" | python3 -c "import sys, json; data=json.load(sys.stdin); print(list(data.keys())[0] if data else '')" 2>/dev/null)
        
        if [ -n "$GREEN_AGENT_ID" ]; then
            check_service "Green Agent Card (to_agent)" "$NGROK_URL/green/to_agent/$GREEN_AGENT_ID/.well-known/agent-card.json"
        fi
        
        if [ -n "$WHITE_AGENT_ID" ]; then
            check_service "White Agent Card (to_agent)" "$NGROK_URL/white/to_agent/$WHITE_AGENT_ID/.well-known/agent-card.json"
        fi
        
        echo ""
        echo "=========================================="
        echo "📋 AgentBeats Registration URLs"
        echo "=========================================="
        echo ""
        echo "Green Agent (Assessor):"
        echo "  Controller URL: $NGROK_URL/green"
        echo "  ✓ Check 'Is Assessor (Green) Agent'"
        echo ""
        echo "White Agent (Task Executor):"
        echo "  Controller URL: $NGROK_URL/white"
        echo "  ☐ Don't check 'Is Assessor (Green) Agent'"
        echo ""
        
    else
        echo -e "${RED}❌ ngrok URL not detected${NC}"
    fi
else
    echo -e "${RED}❌ ngrok not running${NC}"
    echo "   Start with: ngrok http 8100"
fi

echo ""
echo "=========================================="
echo "🔧 Running Processes"
echo "=========================================="
echo ""
echo "Port 8100 (Proxy):"
lsof -i :8100 | grep LISTEN || echo "  Not running"
echo ""
echo "Port 8101 (Green Controller):"
lsof -i :8101 | grep LISTEN || echo "  Not running"
echo ""
echo "Port 8102 (White Controller):"
lsof -i :8102 | grep LISTEN || echo "  Not running"
echo ""
echo "Port 8001 (Green Agent):"
lsof -i :8001 | grep LISTEN || echo "  Not running"
echo ""
echo "Port 8002 (White Agent):"
lsof -i :8002 | grep LISTEN || echo "  Not running"
echo ""

echo "=========================================="
echo "Done!"
echo "=========================================="


