# Green Agent

A comprehensive AI agent platform for travel planning, featuring a dual-agent architecture (Green Agent for evaluation/orchestration and White Agent for reasoning/execution) with a modern React frontend.

## 🌟 Features

- **Dual Agent System**:
  - **🌱 Green Agent**: Orchestrator and evaluator. Manages the conversation flow, evaluates responses against ground truth (fixtures), and provides detailed metrics.
  - **⚪ White Agent**: Reasoning engine. Uses ReAct prompting to plan and execute tools (Flight, Hotel, Restaurant search) to solve user queries.
- **Real-time Streaming**: WebSocket-based communication for live token streaming and tool execution updates.
- **Rich UI/UX**:
  - Clean, chat-based interface built with React and Tailwind CSS.
  - **Trace Ledger**: Detailed view of tool calls, arguments, and execution results.
  - **Evaluation Dashboard**: Visual metrics for correctness, helpfulness, alignment, and safety.
  - **Agent Reasoning**: Transparency into the agent's thought process (Thought/Action/Observation loops).
  - **Live Log Analysis**: The system automatically analyzes backend logs to extract and display structured DataFrame operations and tool logic.
  - **Agent Type Badges**: Color-coded badges for different agent types (User, White Agent, Supervisor, Tool).
  - **Markdown Support**: Full markdown rendering in messages.
  - **Error Handling**: User-friendly error messages.
  - **Auto-scroll**: Automatically scrolls to new messages.
  - **Loading States**: Visual feedback during API calls.
- **Tool Integration**:
  - **Flight Search**: Real-time flight data analysis.
  - **Hotel Search**: Hotel recommendations with pricing and amenities.
  - **Restaurant Search**: Dining options with ratings and reviews.
- **Robust Backend**: FastAPI server with Python-based agent logic, using LangChain and Anthropic Claude.

## 🏗️ Architecture

### Backend (`/backend`)
- **FastAPI**: Handles HTTP requests and WebSocket connections.
- **LangChain/LangGraph**: Manages agent state and execution flows.
- **Anthropic Claude**: Powers the reasoning capabilities.
- **Pandas**: Used for data analysis within tools (DataFrame operations are tracked and visualized).
- **Log Capture**: Custom logging infrastructure (`TeeLogger`) ensures all tool output is captured for real-time analysis.

### Frontend (`/frontend`)
- **React 18**: UI Framework.
- **TypeScript**: For type safety.
- **Tailwind CSS**: For styling.
- **Vite**: Build tool.
- **Recharts**: For data visualization in evaluations.
- **React Router**: For navigation between Green Agent and White Agent pages.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Anthropic API Key
- SerpAPI Key (for real-time search data)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Set up environment variables in `backend/.env`:
```env
ANTHROPIC_API_KEY=your_key_here
SERP_API_KEY=your_key_here
```

Start the server:
```bash
python api_server.py
```
The API will run at `http://localhost:8001`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
The app will open at `http://localhost:5173`.

## 🧭 Navigation

The app has two main pages:

- **🌱 Green Agent (`/`)**: The main interface showing the full agent evaluation loop, trace ledger, and metrics.
- **⚪ White Agent (`/white-agent`)**: A focused view of the reasoning agent's direct output with a clean, minimal chat interface.

## 📡 API Endpoints

### POST `/api/chat`
Chat with the White Agent

**Request:**
```json
{
  "message": "Looking for a flight from Oakland to Newark on 11/7/2025"
}
```

**Response:**
```json
{
  "message": "Found 5 flight options...",
  "agent_type": "white_agent",
  "conversation_length": 2,
  "error": null
}
```

### GET `/api/status`
Get current agent status

### POST `/api/reset`
Reset all agents

## 🎨 Styling

The White Agent page uses:
- **Purple theme** for White Agent messages
- **Blue theme** for user messages  
- **Green theme** for Supervisor messages
- **Orange theme** for Tool messages

All styling is done with Tailwind CSS for consistency with the rest of the app.

## 🛠️ Development

- **Logs**: Backend logs are written to `backend/backend.log` and streamed to the terminal.
- **Trace Analysis**: The backend captures stdout/stderr from tools and uses an LLM to parse execution steps, providing a "glass box" view of the agent's actions in the UI.

### Components

- **WhiteAgentChat** (`/pages/WhiteAgentChat.tsx`): Main chat interface for White Agent with clean, focused UI, agent type badges, real-time messaging, and error handling.
- **Navigation** (`/components/Navigation.tsx`): Top navigation bar with tabs for switching between agents.

### Design Principles

The White Agent page is designed to be:
1. **Simple** - Focus on chat, no complex side panels
2. **Fast** - Direct API calls, minimal overhead
3. **Clear** - Easy to see what each agent is doing
4. **Extensible** - Easy to add new features

## 🔮 Next Steps

Potential enhancements:
- [ ] Add streaming support for real-time responses
- [ ] Show reasoning steps inline
- [ ] Add tool call visualization
- [ ] Export conversation history
- [ ] Add voice input

## 📄 License

[MIT](LICENSE)
