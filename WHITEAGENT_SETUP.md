# White Agent Chat Setup Guide

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
./start_white_agent.sh
```

This will:
1. Start the backend API server on port 8000
2. Start the frontend dev server on port 5173
3. Open both in the background

### Option 2: Manual Setup

#### Backend

```bash
# Activate virtual environment
source venv/bin/activate

# Start backend server
cd backend
python api_server.py
```

#### Frontend

```bash
# Install dependencies (first time only)
cd frontend
npm install

# Start dev server
npm run dev
```

## Access the Application

- **Green Agent** (Full Demo): http://localhost:5173/
- **White Agent** (Reasoning Engine): http://localhost:5173/white-agent

## Features

### White Agent Chat Page

✅ **Clean Interface**: Focused on chat without complex evaluations
✅ **Real-time API**: Direct connection to White Agent backend  
✅ **Agent Badges**: Color-coded messages from different agents
✅ **Markdown Support**: Rich text rendering
✅ **Error Handling**: User-friendly error messages

### Navigation

The app now has a navigation bar to switch between:
- 🌱 **Green Agent** - Full evaluation demo
- ⚪ **White Agent** - Reasoning engine chat

## API Endpoints

### White Agent Chat
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Find me a flight from Oakland to Newark"
}
```

### Green Agent Chat
```http
POST /api/chat/green
Content-Type: application/json

{
  "message": "Find me a flight from Oakland to Newark"
}
```

### Agent Status
```http
GET /api/status
```

### Reset Agents
```http
POST /api/reset
```

## Architecture

```
┌─────────────────────────────────────┐
│         Frontend (React)            │
│  ┌──────────────────────────────┐   │
│  │  Navigation Component        │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  Green Agent Chat Page       │   │
│  │  (Complex evaluations)       │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  White Agent Chat Page       │   │
│  │  (Clean reasoning)           │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
              ↕ HTTP/REST
┌─────────────────────────────────────┐
│      Backend (FastAPI)              │
│  ┌──────────────────────────────┐   │
│  │  /api/chat                   │   │
│  │  → WhiteAgent                │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  /api/chat/green             │   │
│  │  → GreenAgent                │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  LangGraph State Management  │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

## Component Structure

```
frontend/src/
├── App.tsx                    # Router configuration
├── pages/
│   └── WhiteAgentChat.tsx    # White Agent chat page
├── components/
│   ├── Navigation.tsx        # Top navigation bar
│   ├── ChatContainer.tsx     # Green Agent page
│   ├── ChatInput.tsx         # Shared input component
│   ├── ChatMessage.tsx       # Shared message component
│   └── LoadingDots.tsx       # Loading indicator
└── types/
    └── chat.ts               # TypeScript types
```

## Environment Variables

Create a `.env` file in the `backend/chatbot/` directory:

```env
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
SERP_API_KEY=your_key_here
BASE_URL=https://serpapi.com/search
```

## Troubleshooting

### Backend won't start

- Check if port 8000 is already in use: `lsof -i :8000`
- Verify virtual environment is activated: `which python`
- Check environment variables are set

### Frontend won't start

- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check if port 5173 is available: `lsof -i :5173`

### API errors

- Check CORS settings in `api_server.py`
- Verify API endpoint URLs in `WhiteAgentChat.tsx`
- Check browser console for detailed errors

## Development

### Adding New Features

1. **New Agent Type**: Add to `backend/chatbot/models.py`
2. **New Endpoint**: Add to `backend/api_server.py`
3. **New Page**: Create in `frontend/src/pages/`
4. **Update Routes**: Modify `frontend/src/App.tsx`

### Testing

```bash
# Test backend
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

## Next Steps

- [ ] Add WebSocket support for streaming
- [ ] Implement conversation history
- [ ] Add export functionality
- [ ] Create mobile-responsive design
- [ ] Add authentication


