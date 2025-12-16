# AgentBeats Setup Fix

## Issues Found

1. **Wrong Agent ID in Controller URL** - The URL has an old agent ID
2. **Agent doesn't know its public URL** - Environment variables not set

## Fix Steps

### Step 1: Update Controller URL in AgentBeats

In AgentBeats dashboard, update the Controller URL to use the **correct Agent ID**:

**Current (WRONG):**
```
https://f3b9cb88fc0e.ngrok-free.app/to_agent/dbeb42af-28d9-4d3d-83b0-19d8e7bfbcf0
```

**Correct:**
```
https://f3b9cb88fc0e.ngrok-free.app/to_agent/a40647c9-faaf-4011-9dce-6146f5981d77
```

### Step 2: Set Environment Variables

The agent needs to know its public URL. Stop the current Green Agent and restart it with these environment variables:

```bash
# Stop the current Green Agent (Ctrl+C in the terminal running it)

# Set environment variables
export AGENT_URL=https://f3b9cb88fc0e.ngrok-free.app
export CLOUDRUN_HOST=f3b9cb88fc0e.ngrok-free.app
export HTTPS_ENABLED=true

# Restart Green Agent
cd backend
source ../venv/bin/activate
ENABLE_NGROK=true python api_server.py
```

### Step 3: Verify Agent Card

After restarting, verify the agent card has the correct URL:

```bash
curl https://f3b9cb88fc0e.ngrok-free.app/to_agent/a40647c9-faaf-4011-9dce-6146f5981d77/.well-known/agent-card.json | python3 -m json.tool | grep url
```

Should show:
```json
"url": "https://f3b9cb88fc0e.ngrok-free.app/to_agent/a40647c9-faaf-4011-9dce-6146f5981d77"
```

### Step 4: Check Again in AgentBeats

1. Update the Controller URL in AgentBeats to the correct one above
2. Click "Check Again" button
3. It should now show "Controller Reachable: Yes" and load the Agent Card

## Quick Fix Script

You can also use this to restart with the correct env vars:

```bash
# Stop current agent (Ctrl+C)

# Set env vars and restart
export AGENT_URL=https://f3b9cb88fc0e.ngrok-free.app
export CLOUDRUN_HOST=f3b9cb88fc0e.ngrok-free.app
export HTTPS_ENABLED=true
cd backend
source ../venv/bin/activate
ENABLE_NGROK=true python api_server.py
```

## Verification Checklist

- [ ] Controller URL uses correct Agent ID: `a40647c9-faaf-4011-9dce-6146f5981d77`
- [ ] Environment variables are set before starting the agent
- [ ] Agent card endpoint returns correct `url` field
- [ ] AgentBeats shows "Controller Reachable: Yes"
- [ ] Agent Card Content loads successfully

