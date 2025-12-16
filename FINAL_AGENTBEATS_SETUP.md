# Final AgentBeats Setup Checklist

## ✅ All Required Fixes Applied

1. **POST /to_agent/{id} endpoint** ✅ Added
2. **Force Agent Card URL to include /to_agent/{agent_id}** ✅ Updated `get_agent_card()`
3. **AGENT_ID environment variable** ✅ Code reads from env
4. **Remove empty-path routes** ✅ Removed `@app.get("")` and `@app.head("")`
5. **ngrok on port 8001** ✅ (needs to be running)
6. **Valid JSON from root** ✅ (when server is running)

## 🚀 How to Start Everything

### Step 1: Start ngrok Tunnel

In Terminal 1:
```bash
ngrok http 8001
```

Copy the HTTPS URL (e.g., `https://f3b9cb88fc0e.ngrok-free.app`)

### Step 2: Start Green Agent Server

In Terminal 2:
```bash
cd /Users/aryanpanda/green-agent

# Set environment variables (USE YOUR ACTUAL AGENT ID FROM AgentBeats)
export AGENT_ID="de5d9987-0eb5-4d1b-a342-a10fced642c7"  # Replace with your actual agent ID
export AGENT_URL="https://f3b9cb88fc0e.ngrok-free.app"   # Replace with your ngrok URL
export HTTPS_ENABLED=true
export ENABLE_NGROK=true

# Start server
cd backend
source ../venv/bin/activate
python api_server.py
```

### Step 3: Verify Endpoints Work

```bash
# Test root endpoint
curl -s "https://your-ngrok-url.ngrok-free.app/" | python3 -m json.tool | grep url

# Should show:
# "url": "https://your-ngrok-url.ngrok-free.app/to_agent/your-agent-id"

# Test agent card endpoint
curl -s "https://your-ngrok-url.ngrok-free.app/.well-known/agent.json" | python3 -m json.tool | grep url

# Test POST endpoint
curl -X POST "https://your-ngrok-url.ngrok-free.app/to_agent/your-agent-id" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Should return JSON (not 405)
```

### Step 4: Configure AgentBeats

In AgentBeats dashboard:
- **Controller URL**: `https://your-ngrok-url.ngrok-free.app` (base URL only, NO `/to_agent/...`)
- Click **"Check Again"**

## ✅ Expected Results

After all steps:
- ✅ Controller Reachable: **Yes**
- ✅ Agent Card Content: **Loaded** (no more error)
- ✅ Hosted Status: **Ready** (not pending)
- ✅ Assessment: Can start immediately

## 🔧 Quick Restart Script

Save this as `restart_for_agentbeats.sh`:

```bash
#!/bin/bash
cd /Users/aryanpanda/green-agent

# Kill existing processes
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

# Set environment variables (UPDATE THESE!)
export AGENT_ID="de5d9987-0eb5-4d1b-a342-a10fced642c7"
export AGENT_URL="https://f3b9cb88fc0e.ngrok-free.app"
export HTTPS_ENABLED=true
export ENABLE_NGROK=true

# Start server
cd backend
source ../venv/bin/activate
python api_server.py
```

Make it executable:
```bash
chmod +x restart_for_agentbeats.sh
```

## ⚠️ Important Notes

1. **Agent ID must match**: The `AGENT_ID` env var must match the Agent ID in your AgentBeats dashboard
2. **ngrok URL changes**: Each time you restart ngrok, update `AGENT_URL` and restart the server
3. **Both must be running**: ngrok tunnel AND the backend server must both be running
4. **Controller URL**: Use only the base URL in AgentBeats (no `/to_agent/...` path)

## 🐛 Troubleshooting

### ngrok shows "offline"
- Make sure backend server is running on port 8001
- Restart ngrok: `ngrok http 8001`
- Verify: `curl http://localhost:8001/health` should return `{"status":"healthy"}`

### Agent Card URL doesn't include /to_agent/{id}
- Make sure `AGENT_ID` environment variable is set
- Restart the server after setting env vars
- Verify: `curl https://your-url/ | python3 -m json.tool | grep url`

### POST returns 405
- Server needs to be restarted after code changes
- Verify POST endpoint: `curl -X POST https://your-url/to_agent/{id} -d '{}'`

### AgentBeats still shows "Agent Card Content could not be loaded"
- Wait 10-30 seconds after restarting (cache/validation delay)
- Check that root endpoint returns valid JSON with `url` field
- Verify the `url` field includes `/to_agent/{agent_id}`

