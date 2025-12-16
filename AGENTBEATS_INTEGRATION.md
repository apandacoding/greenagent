# AgentBeats Controller Integration

This document explains how the Green Agent and White Agent are integrated with AgentBeats controller.

## Overview

The AgentBeats controller is a lightweight local component that:
1. **Exposes a service API** for displaying and managing agent process state
2. **Detects and launches** the local agent using the `run.sh` script
3. **Proxies requests** to the agent - useful when deploying as a microservice
4. **Provides a management UI** for debugging and monitoring your agent

## Architecture

```
┌─────────────────────────────────────┐
│  AgentBeats Controller (Port 8101) │
│  - Management UI                    │
│  - Process control (/agents)       │
│  - Request proxy                    │
└──────────────┬──────────────────────┘
               │ spawns
               ↓
       ┌──────────────┐
       │  run_green.sh │
       │  or           │
       │  run_white.sh │
       └──────┬───────┘
              │ launches
              ↓
     ┌────────────────────┐
     │  a2a_main.py run   │
     │  (Port 8001/8002)  │
     └────────────────────┘
```

## Files Created

### 1. `run_green.sh` and `run_white.sh`
These are the agent startup scripts called by the AgentBeats controller. They:
- Set the `ROLE` environment variable (green or white)
- Execute `python a2a_main.py run`
- Use `$HOST` and `$AGENT_PORT` provided by the controller

### 2. `start_agentbeats_green.sh` and `start_agentbeats_white.sh`
These are convenience scripts to launch the agents with the AgentBeats controller. They:
- Set default ports (8001 for green agent, 8002 for white agent)
- Set controller ports (8101 for green, 8102 for white)
- Launch `agentbeats run_ctrl`

### 3. `requirements.txt`
Updated to include `earthshaker` package (the AgentBeats runtime).

## Installation

1. Install the AgentBeats package:
```bash
pip install earthshaker
```

Or install all requirements:
```bash
cd backend
pip install -r requirements.txt
```

## Usage

### Starting Green Agent with Controller

```bash
./start_agentbeats_green.sh
```

This will:
- Start the green agent on port 8001
- Start the controller on port 8101
- Open the management UI at `http://localhost:8101`

### Starting White Agent with Controller

```bash
./start_agentbeats_white.sh
```

This will:
- Start the white agent on port 8002
- Start the controller on port 8102
- Open the management UI at `http://localhost:8102`

### Custom Port Configuration

You can override the default ports:

```bash
# For green agent
AGENT_PORT=9001 CTRL_PORT=9101 ./start_agentbeats_green.sh

# For white agent
AGENT_PORT=9002 CTRL_PORT=9102 ./start_agentbeats_white.sh
```

## AgentBeats Controller Features

Once running, you can access the controller at `http://localhost:8101` (or 8102 for white agent).

### Management UI
- View agent status (running/stopped)
- Start/stop/restart the agent
- View recent logs
- Access the agent card

### API Endpoints

The controller exposes these endpoints:

#### Status Endpoints
- `GET /status` - Overall controller status
- `GET /agents` - List of managed agents
- `GET /agents/{agent_id}` - Specific agent status
- `POST /agents/{agent_id}/reset` - Reset agent state

#### Agent Card Endpoints
- `GET /.well-known/agent-card.json` - Agent card
- `GET /to_agent/{agent_id}` - Agent-specific card
- `GET /to_agent/{agent_id}/.well-known/agent-card.json` - Agent card with ID

#### A2A Protocol Endpoints
- `POST /to_agent/{agent_id}` - Send JSON-RPC request to agent

## Deployment

### For Public Deployment

When deploying to make your agent accessible over the network:

1. **Use Cloud VM with Public IP**
   - Provision a cloud VM (e.g., AWS EC2, Google Cloud Compute Engine)
   - Configure public IP or domain name
   - Obtain SSL certificate for HTTPS

2. **Using Docker/Container**
   ```dockerfile
   # Create Procfile
   web: agentbeats run_ctrl
   ```

3. **Using Google Cloud Run**
   - Use Google Cloud Buildpacks to build image
   - Push to Artifact Registry
   - Deploy as Cloud Run service (HTTPS automatic)

### Environment Variables for Deployment

Set these in your deployment environment:

```bash
ROLE=green              # or white
AGENT_URL=https://your-domain.com
HOST=0.0.0.0
AGENT_PORT=8001         # or 8002 for white
```

## Publishing to AgentBeats Platform

Once your agent is publicly accessible with the controller:

1. Go to AgentBeats website
2. Fill out the publish form
3. Provide your public controller URL
4. Your agent is now discoverable on AgentBeats! 🚀

## Testing Controller Integration

### Check if controller is working:
```bash
curl http://localhost:8101/status
```

### Check agent list:
```bash
curl http://localhost:8101/agents
```

### Check agent card:
```bash
curl http://localhost:8101/.well-known/agent-card.json
```

### Reset agent:
```bash
curl -X POST http://localhost:8101/agents/{agent_id}/reset
```

## Troubleshooting

### Controller won't start
- Ensure `earthshaker` is installed: `pip install earthshaker`
- Check if port is already in use: `lsof -i :8101`

### Agent won't start
- Check the controller UI for error messages
- Verify `run_green.sh` or `run_white.sh` is executable
- Check that `a2a_main.py` exists in `backend/` directory

### Can't access management UI
- Verify controller is running: `curl http://localhost:8101/status`
- Check firewall settings if accessing remotely
- Ensure CTRL_PORT is not blocked

## Integration with Existing Scripts

The AgentBeats integration is separate from your existing launch scripts:

- **Existing**: `start_green_agent_with_env.sh`, `start_ngrok_*.sh`, etc.
- **AgentBeats**: `start_agentbeats_green.sh`, `start_agentbeats_white.sh`

You can use either approach depending on your needs:
- Use existing scripts for local development/testing
- Use AgentBeats scripts for deployment and public access

## Next Steps

1. ✅ Install earthshaker: `pip install earthshaker`
2. ✅ Test locally: `./start_agentbeats_green.sh`
3. ✅ Access UI: `http://localhost:8101`
4. 🚀 Deploy with public URL
5. 🚀 Publish on AgentBeats platform

## References

- [AgentBeats Documentation](https://agentbeats.dev/docs)
- [Integrate Your A2A Agents with AgentBeats](https://agentbeats.dev/docs/integrate-a2a-agents)
- [earthshaker PyPI Package](https://pypi.org/project/earthshaker/)


