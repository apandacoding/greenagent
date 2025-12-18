# 🟢 Green Agent

A dual-agent AI platform for travel planning with built-in evaluation. The **Green Agent** (Assessor) orchestrates and evaluates the **White Agent** (Task Executor) which uses tools to fulfill user requests.

---

y## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GREEN AGENT SYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   🟢 GREEN AGENT (Assessor/Orchestrator)                                    │
│   ├── Receives user queries                                                 │
│   ├── Delegates to White Agent                                              │
│   ├── Evaluates responses (5 criteria)                                      │
│   └── Returns scores + reasoning                                            │
│                                                                             │
│   ⚪ WHITE AGENT (Task Executor) - Embedded in Green Agent                  │
│   ├── ReAct reasoning loop (Thought → Action → Observation)                 │
│   ├── Tool execution: 🛫 Flights | 🏨 Hotels | 🍽️ Restaurants                │
│   └── Supervisor validation with retry capability                           │
│                                                                             │
│   📊 EVALUATION ENGINE                                                      │
│   ├── Correctness (0-10)   - Factual accuracy                               │
│   ├── Helpfulness (0-10)   - Addresses user needs                           │
│   ├── Tool Usage (0-10)    - Proper tool selection & execution              │
│   ├── Alignment (0-10)     - Follows guidelines                             │
│   └── Safety (0-10)        - No harmful content                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| Anthropic API Key | - | Claude LLM for reasoning |
| SerpAPI Key | - | Real-time search data (flights, hotels, restaurants) |

---

## 🚀 Quick Start

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/your-repo/green-agent.git
cd green-agent

# Create and activate virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

y### 2. Configure Environment Variables

Create `backend/.env`:

```env
yy# Required
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
SERP_API_KEY=your-serpapi-key-here

# Optional (defaults shown)
GREEN_AGENT_PORT=8001
WHITE_AGENT_PORT=8002
```

### 3. Run the Application

#### Option A: Frontend + Backend (Full App)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python api_server.py
```
Backend runs at `http://localhost:8001`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`

#### Option B: Green Agent Only (A2A Mode for AgentBeats)

```bash
cd backend
source venv/bin/activate
python a2a_green_agent.py
```
Green Agent A2A server runs at `http://localhost:8001`

#### Option C: White Agent Only (A2A Mode for AgentBeats)

```bash
cd backend
source venv/bin/activate
python a2a_white_agent.py
```
White Agent A2A server runs at `http://localhost:8002`

#### Option D: Both Agents (Separate A2A Servers)

**Terminal 1:**
```bash
cd backend && source venv/bin/activate
python a2a_green_agent.py  # Port 8001
```

**Terminal 2:**
```bash
cd backend && source venv/bin/activate
python a2a_white_agent.py  # Port 8002
```

---

## 🔌 API Endpoints

### Main API Server (`api_server.py` - Port 8001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message to Green Agent (includes evaluation) |
| `/api/white-chat` | POST | Send message directly to White Agent |
| `/api/status` | GET | Get current agent status |
| `/api/reset` | POST | Reset all agent conversations |
| `/ws/chat` | WebSocket | Real-time streaming chat |

#### Example: Chat Request

```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find flights from SFO to JFK for January 23-26, 2026"}'
```

#### Example Response

```json
{
  "message": "# Your Complete Trip Plan...",
  "agent_type": "green_agent",
  "conversation_length": 2,
  "white_agent_response": "Here are the flight options...",
  "evaluation_result": {
    "aggregatedScore": 9.2,
    "scoreBreakdown": {
      "correctness": { "score": 9, "reasoning": "..." },
      "helpfulness": { "score": 9, "reasoning": "..." },
      "tool_usage": { "score": 10, "reasoning": "..." },
      "alignment": { "score": 9, "reasoning": "..." },
      "safety": { "score": 9, "reasoning": "..." }
    }
  }
}
```

### A2A Protocol Endpoints (AgentBeats Compatible)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | POST | JSON-RPC message handling |
| `/.well-known/agent-card.json` | GET | Agent metadata card |
| `/status` | GET | Health check |
| `/agents/{id}/reset` | POST | Reset specific agent |

---

## 🗂️ Project Structure

```
green-agent/
├── backend/
│   ├── api_server.py           # Main FastAPI server (WebSocket + REST)
│   ├── a2a_green_agent.py      # Green Agent A2A server (AgentBeats)
│   ├── a2a_white_agent.py      # White Agent A2A server (AgentBeats)
│   ├── chatbot/
│   │   ├── agent.py            # WhiteAgent + GreenAgent classes
│   │   ├── models.py           # Pydantic models
│   │   ├── tools.py            # LangChain tool wrappers
│   │   └── config.py           # Configuration settings
│   ├── tools/
│   │   ├── flights.py          # Flight search implementation
│   │   ├── hotels.py           # Hotel search implementation
│   │   └── restaurant.py       # Restaurant search implementation
│   ├── green_agent/
│   │   ├── streaming/          # WebSocket event streaming
│   │   ├── analysis/           # Log analysis & trace extraction
│   │   └── execution/          # Trace ledger management
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/              # React page components
│   │   └── components/         # Reusable UI components
│   └── package.json
├── docs/
│   ├── GREEN_AGENT_ARCHITECTURE.md
│   └── WHITE_AGENT_ARCHITECTURE.md
└── README.md
```

---

## 🎯 How It Works

### 1. User sends a query
```
"Plan a trip from SFO to NYC, staying in Chelsea, with Indian restaurants"
```

### 2. Green Agent orchestrates
- Passes query to embedded White Agent
- Waits for complete response

### 3. White Agent executes (ReAct Loop)
```
Thought: I need to search for flights from SFO to NYC
Action: flight_search("SFO to JFK flights")
Observation: Found 8 flights, cheapest $219 on Alaska...

Thought: Now I need hotels in Chelsea
Action: hotel_search("Chelsea NYC budget hotels")
Observation: Found 18 hotels, cheapest $51/night...

Thought: Finally, Indian restaurants
Action: restaurant_search("Indian restaurants Chelsea NYC")
Observation: Found 5 restaurants, top rated Cloves 4.8⭐...

Final Answer: Here's your complete trip plan...
```

### 4. Green Agent evaluates
- Receives White Agent's response + tool execution trace
- Scores across 5 criteria using Claude
- Returns aggregated score + detailed reasoning

### 5. Response sent to user
- White Agent's trip plan
- Evaluation scores and breakdown
- Tool execution trace (optional)

---

## 🧪 Testing

### Test the API directly

```bash
# Health check
curl http://localhost:8001/api/status

# Send a chat message
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find flights from Oakland to Newark on November 7, 2025"}'

# Reset conversation
curl -X POST http://localhost:8001/api/reset
```

### Test A2A endpoints (AgentBeats)

```bash
# Get agent card
curl http://localhost:8001/.well-known/agent-card.json

# Send JSON-RPC message
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"text": "Find flights to NYC"}]
      }
    },
    "id": "1"
  }'
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | - | Claude API key |
| `SERP_API_KEY` | ✅ | - | SerpAPI key for search tools |
| `GREEN_AGENT_PORT` | ❌ | 8001 | Green Agent server port |
| `WHITE_AGENT_PORT` | ❌ | 8002 | White Agent server port |
| `LOG_LEVEL` | ❌ | INFO | Logging verbosity |

### Customizing Evaluation Criteria

Edit `backend/chatbot/agent.py` → `_evaluate_output()` method to modify:
- Scoring rubrics
- Criteria weights
- Evaluation prompts

---

## 🌐 AgentBeats Integration

For integration with [AgentBeats](https://agentbeats.com) platform:

### 1. Expose agents via ngrok

```bash
# Terminal 1: Start Green Agent
cd backend && python a2a_green_agent.py

# Terminal 2: Start ngrok tunnel
ngrok http 8001
```

### 2. Register with AgentBeats

Use the ngrok URL (e.g., `https://abc123.ngrok.io`) to register your agent on the AgentBeats platform.

### 3. Agent Cards

- **Green Agent**: Assessment agent that evaluates White Agent outputs
- **White Agent**: Travel planning agent with flight/hotel/restaurant tools

---

## 📊 Frontend Features

- **Chat Interface**: Clean, message-based UI
- **Trace Ledger**: View all tool calls and their outputs
- **Evaluation Dashboard**: Visual scores with reasoning
- **Agent Badges**: Color-coded for different agent types
- **Real-time Streaming**: WebSocket-based live updates
- **Markdown Rendering**: Rich text in responses

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure venv is activated: `source venv/bin/activate` |
| `ANTHROPIC_API_KEY not set` | Create `.env` file in `backend/` directory |
| Port already in use | Kill existing process: `lsof -ti:8001 \| xargs kill` |
| WebSocket connection failed | Check CORS settings in `api_server.py` |

### Logs

Backend logs are written to `backend/backend.log` and streamed to terminal.

```bash
# View live logs
tail -f backend/backend.log

# Search for errors
grep -i error backend/backend.log
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add my feature"`
4. Push to branch: `git push origin feature/my-feature`
5. Open a Pull Request
