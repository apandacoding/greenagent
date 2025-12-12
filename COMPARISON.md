# Comparison: Custom FastAPI vs AgentBeats Framework

## Overview

This document compares your **custom FastAPI server** (`/Users/aryanpanda/green-agent/backend/api_server.py`) with the **AgentBeats framework example** (`/Users/aryanpanda/agentify-example-tau-bench`).

---

## Architecture Comparison

### Custom FastAPI Server (Port 8001)

**Location:** `/Users/aryanpanda/green-agent/backend/api_server.py`

**Structure:**
- Direct FastAPI implementation
- Custom endpoint handlers
- Manual AgentBeats compatibility layer
- Uses your existing `GreenAgent` and `WhiteAgent` classes

**Key Features:**
- ✅ Full control over endpoints
- ✅ Direct integration with your existing agent logic
- ✅ Custom evaluation using `GreenAgent._evaluate_output()`
- ✅ WebSocket support for real-time communication
- ✅ Dual decorators for root endpoint (handles trailing slash issue)

**Endpoints:**
```python
GET  /              # Agent Card metadata (dual decorators: "" and "/")
GET  /status        # Agent status
GET  /health        # Health check
POST /assess        # Assessment endpoint (AgentBeats compatible)
POST /api/chat      # Chat endpoint
POST /api/reset     # Reset endpoint
WS   /ws/green      # WebSocket for real-time updates
```

**AgentBeats Compatibility:**
- ✅ Root endpoint returns Agent Card JSON
- ✅ `/status` endpoint for health checks
- ✅ `/assess` endpoint with proper payload handling
- ✅ Handles trailing slash issue (dual decorators)
- ✅ Returns proper JSON format expected by AgentBeats

---

### AgentBeats Framework (Port 8010)

**Location:** `/Users/aryanpanda/agentify-example-tau-bench`

**Structure:**
- Uses A2A (Agent-to-Agent) protocol
- `A2AStarletteApplication` wrapper
- Agent Card defined in TOML file
- Built-in AgentBeats compatibility

**Key Features:**
- ✅ Standardized A2A protocol
- ✅ Automatic endpoint generation
- ✅ Agent Card from TOML configuration
- ✅ Built-in task store and event queue
- ✅ Framework handles AgentBeats integration

**Endpoints (A2A Protocol):**
- A2A protocol endpoints (automatically generated)
- Agent Card endpoint (from TOML)
- Task execution endpoints
- Event streaming endpoints

**Agent Card Configuration:**
```toml
# src/green_agent/tau_green_agent.toml
name = "tau_green_agent"
description = "The assessment hosting agent for tau-bench."
version = "0.1.0"
defaultInputModes = ["text"]
defaultOutputModes = ["text"]
```

---

## Key Differences

| Aspect | Custom FastAPI | AgentBeats Framework |
|--------|---------------|---------------------|
| **Protocol** | REST API + WebSocket | A2A Protocol |
| **Endpoint Definition** | Manual FastAPI routes | Automatic (A2A framework) |
| **Agent Card** | Hardcoded in Python | TOML configuration file |
| **Evaluation Logic** | Your `GreenAgent._evaluate_output()` | Tau-bench specific evaluation |
| **Complexity** | More control, more code | Less code, framework handles details |
| **Flexibility** | Full customization | Framework constraints |
| **AgentBeats Integration** | Manual compatibility layer | Built-in support |
| **Trailing Slash Fix** | Dual decorators (`@app.get("")` and `@app.get("/")`) | Framework handles automatically |

---

## Code Comparison

### Root Endpoint

**Custom FastAPI:**
```python
@app.get("")
@app.get("/")
async def root():
    return {
        "name": "Green Travel Agent",
        "description": "AI agent for travel planning...",
        "version": "1.0.0",
        "endpoints": {...},
        "agent_type": "assessor",
        "capabilities": [...]
    }
```

**AgentBeats Framework:**
```python
# Automatically generated from AgentCard TOML
agent_card_dict = load_agent_card_toml(agent_name)
app = A2AStarletteApplication(
    agent_card=AgentCard(**agent_card_dict),
    ...
)
```

### Assessment Endpoint

**Custom FastAPI:**
```python
@app.post("/assess")
async def assess_endpoint(req: AssessRequest):
    # Manual payload extraction
    task_id = req.task.get("id", "unknown")
    task_instructions = req.task.get("instructions", "")
    
    # Use your GreenAgent evaluation
    eval_result = await green_agent._evaluate_output(eval_state)
    
    # Convert to AgentBeats format
    return {
        "total_score": ...,
        "breakdown": {...},
        "trace": {},
        "feedback": "..."
    }
```

**AgentBeats Framework:**
```python
class TauGreenAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        # Framework handles request parsing
        user_input = context.get_user_input()
        tags = parse_tags(user_input)
        
        # Tau-bench specific evaluation
        res = await ask_agent_to_solve(white_agent_url, env, task_index)
        
        # Framework handles response formatting
```

---

## Recommendations

### Use Custom FastAPI If:
- ✅ You want full control over endpoints
- ✅ You need to integrate with existing agent logic
- ✅ You want WebSocket support
- ✅ You prefer direct FastAPI patterns
- ✅ You need custom evaluation logic

### Use AgentBeats Framework If:
- ✅ You want standardized A2A protocol
- ✅ You prefer framework-managed endpoints
- ✅ You want built-in AgentBeats compatibility
- ✅ You're building a new agent from scratch
- ✅ You want less boilerplate code

---

## Current Status

### Custom FastAPI Server
- ✅ Running on port 8001
- ✅ Cloudflare tunnel: `generations-manuals-pleased-ecommerce.trycloudflare.com`
- ✅ All endpoints working
- ✅ AgentBeats compatible

### AgentBeats Framework Example
- ✅ Running on port 8010
- ✅ Cloudflare tunnel: (check output for URL)
- ✅ Framework endpoints active
- ✅ Tau-bench specific implementation

---

## Next Steps

1. **Test both implementations** with AgentBeats dashboard
2. **Compare behavior** - see which one AgentBeats prefers
3. **Decide on approach** - custom vs framework
4. **Optimize chosen approach** based on test results

