# Deploy Green Agent to AgentBeats v2

This guide shows you how to expose your AgentBeats controller publicly using ngrok and register it on AgentBeats v2.

## Prerequisites

✅ AgentBeats controller working locally  
✅ ngrok installed ([download here](https://ngrok.com/download))  
✅ Your ngrok authtoken: `36rEdd2UeQf9wiIMTcLzZuSFDQI_Fz4swVHo5ba3Lju3NuSx`

## Step 1: Configure ngrok

```bash
./setup_ngrok_agentbeats.sh
```

This adds your authtoken to ngrok.

## Step 2: Start Controller with ngrok

```bash
./start_agentbeats_green_ngrok.sh
```

This will:
1. ✅ Start the AgentBeats controller on port 8101
2. ✅ Start your green agent on port 8001
3. ✅ Create an ngrok tunnel to expose port 8101 publicly
4. ✅ Display your public URL

You'll see output like:

```
🌐 Public Controller URL: https://abc123.ngrok-free.app

📋 Use this URL to register on AgentBeats:
   Controller URL: https://abc123.ngrok-free.app
```

## Step 3: Verify It Works

### Local Test (Should Still Work):
```bash
# Controller status
curl http://localhost:8101/status

# Agent list
curl http://localhost:8101/agents

# Management UI
open http://localhost:8101
```

### Public Test (Through ngrok):
```bash
# Replace with your actual ngrok URL
NGROK_URL="https://abc123.ngrok-free.app"

# Test controller status
curl $NGROK_URL/status

# Test agents endpoint
curl $NGROK_URL/agents

# Test agent card
curl $NGROK_URL/.well-known/agent-card.json
```

## Step 4: Register on AgentBeats v2

Go to AgentBeats and fill in the form:

### Required Fields:

**Name:** `Green Travel Agent` (or your preferred name)

**Deploy Type:** `Remote`

**✓ Is Assessor (Green) Agent** ← Check this box!

**Controller URL:** `https://your-ngrok-url.ngrok-free.app`  
(Use the URL from Step 2)

**Git URL (optional):** `https://github.com/yourusername/green-agent` (if you want)

**Git Branch (optional):** `main`

Click **"Create Agent"**

## Step 5: Test from AgentBeats

Once registered, AgentBeats will:
1. Connect to your controller URL
2. Query the `/agents` endpoint
3. Get your agent card from `/.well-known/agent-card.json`
4. Show your agent as available for assessments

## Important Notes

### ngrok Free Tier Limitations:
- ⚠️ URL changes every time you restart ngrok
- ⚠️ Session expires after 2 hours
- ⚠️ Need to update AgentBeats registration if URL changes

### For Production:
Consider these alternatives:
- **ngrok Paid Plan** - Get a static domain
- **Google Cloud Run** - Free HTTPS with static URL
- **AWS EC2 + Nginx** - Full control with your own domain

### Keeping It Running:

The script will run until you press Ctrl+C. To run in background:

```bash
# Start in background (detached)
nohup ./start_agentbeats_green_ngrok.sh > logs/startup.log 2>&1 &

# Check if running
curl http://localhost:8101/status

# Get ngrok URL
curl http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok-free\.app'
```

## Troubleshooting

### "ngrok not found"
Install ngrok:
```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

### "Controller failed to start"
Check the logs:
```bash
tail -f logs/green_controller_ngrok.log
```

Common issues:
- Missing `agentbeats` package: Make sure venv is activated
- Port 8101 already in use: Kill existing process or use different port

### "Agent shows as error"
Test the agent directly:
```bash
# Activate venv
source venv/bin/activate

# Test agent startup
cd backend
export ROLE=green
export HOST=0.0.0.0
export AGENT_PORT=8001
python a2a_main.py run
```

### ngrok URL Changes
If you restart ngrok, you'll get a new URL. You'll need to:
1. Get the new URL from the output or `http://localhost:4040`
2. Update your agent registration on AgentBeats

## Architecture

```
AgentBeats Platform
        ↓
    (Internet)
        ↓
ngrok Tunnel (https://xxx.ngrok-free.app)
        ↓
AgentBeats Controller (localhost:8101)
        ↓
Green Agent (localhost:8001)
```

## Quick Commands Reference

```bash
# Setup (one time)
./setup_ngrok_agentbeats.sh

# Start with ngrok
./start_agentbeats_green_ngrok.sh

# Test locally
curl http://localhost:8101/status
curl http://localhost:8101/agents

# View ngrok dashboard
open http://localhost:4040

# View controller UI
open http://localhost:8101

# Check logs
tail -f logs/green_controller_ngrok.log
tail -f logs/ngrok.log

# Stop everything
# Press Ctrl+C in the terminal running the script
```

## Expected AgentBeats Registration Flow

1. **You provide** Controller URL: `https://xxx.ngrok-free.app`
2. **AgentBeats queries** `https://xxx.ngrok-free.app/agents`
3. **Controller responds** with agent info:
   ```json
   {
     "green_agent": {
       "id": "green_agent",
       "state": "running",
       "url": "http://0.0.0.0:8001",
       "internal_port": 8001
     }
   }
   ```
4. **AgentBeats discovers** your agent card at `/.well-known/agent-card.json`
5. **Your agent is live** and ready for assessments! 🎉

## Monitoring

While running, you can monitor:
- **Controller UI**: http://localhost:8101
- **ngrok Dashboard**: http://localhost:4040
- **Controller Logs**: `tail -f logs/green_controller_ngrok.log`
- **Agent Status**: `curl http://localhost:8101/agents`

## Next Steps After Registration

Once registered on AgentBeats:
1. ✅ Your agent appears in the AgentBeats agent list
2. ✅ Others can select your agent for assessments
3. ✅ AgentBeats will send reset/start/stop commands via the controller API
4. ✅ Your agent participates in battles and evaluations

That's it! Your Green Agent is now live on AgentBeats v2! 🚀


