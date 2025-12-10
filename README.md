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

# Install dependencies (ensure you have necessary packages)
pip install fastapi uvicorn langchain langchain-anthropic anthropic pandas python-dotenv requests tabulate
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

- **Green Agent (`/`)**: The main interface showing the full agent evaluation loop, trace ledger, and metrics.
- **White Agent (`/white-agent`)**: A focused view of the reasoning agent's direct output.

## 🛠️ Development

- **Logs**: Backend logs are written to `backend/backend.log` and streamed to the terminal.
- **Trace Analysis**: The backend captures stdout/stderr from tools and uses an LLM to parse execution steps, providing a "glass box" view of the agent's actions in the UI.

## 📄 License

[MIT](LICENSE)

