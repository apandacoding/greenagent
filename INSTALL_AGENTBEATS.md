# AgentBeats Installation Guide

## The Issue You Hit

You tried to install `earthshaker` but it requires Python 3.13+. Your system uses Python 3.12.

## Solution

I've created a **custom AgentBeats-compatible controller** that works with Python 3.12+ at `backend/agentbeats_controller.py`.

## Installation Steps

### Step 1: Install the AgentBeats Package

The `agentbeats` package from the official repository includes the A2A protocol framework.

**In your terminal (NOT through pip in this README):**

```bash
# Use your system Python (3.11) which has most packages installed
pip install agentbeats
```

If you get SSL errors, try:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org agentbeats
```

### Step 2: Verify Installation

```bash
# Test that you can import the a2a module from agentbeats
python3.11 -c "from a2a.server.apps import A2AStarletteApplication; print('✅ AgentBeats A2A module OK')"
```

## Running Your Agents

### Option 1: Start Green Agent
```bash
./start_agentbeats_green.sh
```

Then visit: `http://localhost:8101` for the management UI

### Option 2: Start White Agent
```bash
./start_agentbeats_white.sh
```

Then visit: `http://localhost:8102` for the management UI

### Option 3: Start Both Agents
```bash
./start_both_agentbeats.sh
```

## What Was Fixed

1. ✅ **Custom Controller**: Created `backend/agentbeats_controller.py` that works with Python 3.12
2. ✅ **Run Scripts**: Updated `run_green.sh` and `run_white.sh` to use python3.11
3. ✅ **Startup Scripts**: Modified all startup scripts to use the custom controller
4. ✅ **Requirements**: Added `agentbeats>=1.2.0` to requirements.txt

## Troubleshooting

### "ModuleNotFoundError: No module named 'a2a'"

The agentbeats package provides the a2a module. Install it:
```bash
pip install agentbeats
```

### "ModuleNotFoundError: No module named 'uvicorn'"

Install uvicorn (should be included with agentbeats):
```bash
pip install uvicorn
```

### Agent won't start - "state: error"

Check the agent logs to see what failed:
```bash
# The controller tries to run ./run_green.sh
# Test it manually:
export ROLE=green
export HOST=0.0.0.0
export AGENT_PORT=8001
./run_green.sh
```

### Different Python environments

Your system has multiple Python installations:
- `/opt/homebrew/bin/python3.11` - Homebrew Python 3.11 (has most packages)
- Python 3.12 (Poetry/terminus venv)
- Python 3.13 (venv)

The scripts now prefer `python3.11` which has all the packages installed globally.

## Testing the Controller

Once running, test these endpoints:

```bash
# Controller status
curl http://localhost:8101/status

# List agents
curl http://localhost:8101/agents

# Agent card (through agent directly)
curl http://localhost:8001/.well-known/agent-card.json

# Visit management UI
open http://localhost:8101
```

## Next Steps

1. Install `agentbeats`: `pip install agentbeats` (in your terminal)
2. Test the green agent: `./start_agentbeats_green.sh`
3. Open the UI: `http://localhost:8101`
4. Check if agent is running: Look for "running" state in the UI

## Architecture

```
You run:
  ./start_agentbeats_green.sh
     ↓
  Custom Controller starts (port 8101)
     ↓
  Controller spawns ./run_green.sh
     ↓
  run_green.sh executes: python3.11 backend/a2a_main.py run
     ↓
  a2a_main.py starts your green agent (port 8001)
     ↓
  Agent is now accessible at http://localhost:8001
  Management UI at http://localhost:8101
```

The controller provides:
- Process management (start/stop/restart)
- Management UI with status
- API endpoints for AgentBeats platform
- Easy reset between assessment runs


