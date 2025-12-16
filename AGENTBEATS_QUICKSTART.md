# AgentBeats Integration - Quick Start Guide

## 3-Step Integration ✅ Complete!

Your Green Agent and White Agent are now wrapped with AgentBeats controller!

## Installation

```bash
# Install AgentBeats SDK (includes A2A protocol)
pip install agentbeats

# Note: earthshaker requires Python 3.13+, so we use agentbeats instead
# This provides the same A2A protocol functionality

# Or install all dependencies
cd backend && pip install -r requirements.txt
```

## Launch Your Agents

### Green Agent (Assessment/Evaluator)
```bash
./start_agentbeats_green.sh
```
- **Agent Port**: 8001
- **Controller Port**: 8101
- **Management UI**: http://localhost:8101

### White Agent (Task Executor)
```bash
./start_agentbeats_white.sh
```
- **Agent Port**: 8002
- **Controller Port**: 8102
- **Management UI**: http://localhost:8102

### Run Both Agents
```bash
# Terminal 1
./start_agentbeats_green.sh

# Terminal 2  
./start_agentbeats_white.sh
```

## What's Included

✅ **Agent Scripts**: `run_green.sh` and `run_white.sh`  
✅ **Startup Scripts**: `start_agentbeats_green.sh` and `start_agentbeats_white.sh`  
✅ **Dependencies**: `earthshaker` added to `requirements.txt`  
✅ **Environment Support**: Uses `$HOST` and `$AGENT_PORT`

## Quick Test

```bash
# Start green agent
./start_agentbeats_green.sh

# In another terminal, test it
curl http://localhost:8101/status
curl http://localhost:8101/.well-known/agent-card.json
```

## Key Features

🎯 **Process Management**: Start/stop/restart agents via API or UI  
🔄 **Easy Reset**: Reset agent state without restarting  
📊 **Monitoring**: View agent status and logs  
🌐 **Request Proxy**: All requests route through controller  
🚀 **Deploy Ready**: Ready for cloud deployment

## Next Steps

1. ✅ **Test Locally**: Run the startup scripts above
2. 🚀 **Deploy**: Use cloud VM or container platform
3. 🌐 **Go Public**: Get HTTPS URL for your controller
4. 📢 **Publish**: Register on AgentBeats platform

## Architecture

```
User Request → AgentBeats Controller → Your Agent
              (Port 8101/8102)         (Port 8001/8002)
```

The controller:
- Manages agent lifecycle
- Provides management UI
- Proxies all requests
- Enables easy resets

## File Structure

```
green-agent/
├── run_green.sh                    # Green agent launcher
├── run_white.sh                    # White agent launcher
├── start_agentbeats_green.sh       # Start green with controller
├── start_agentbeats_white.sh       # Start white with controller
├── backend/
│   ├── a2a_main.py                 # Main entry point
│   ├── a2a_green_agent.py          # Green agent A2A impl
│   ├── a2a_white_agent.py          # White agent A2A impl
│   └── requirements.txt            # Includes earthshaker
└── AGENTBEATS_INTEGRATION.md       # Full documentation
```

## Troubleshooting

**Controller won't start?**
```bash
pip install earthshaker
```

**Port already in use?**
```bash
# Use custom ports
AGENT_PORT=9001 CTRL_PORT=9101 ./start_agentbeats_green.sh
```

**Need help?**
See `AGENTBEATS_INTEGRATION.md` for detailed documentation.

---

**You're ready to go! 🎉**

Start your agents and visit the management UI to see them in action.


