# White Agent Chat Page

A clean, modern chat interface for the White Agent reasoning engine.

## Features

✅ **Real-time Chat**: Stream responses from the White Agent backend
✅ **Agent Type Badges**: Color-coded badges for different agent types (User, White Agent, Supervisor, Tool)
✅ **Markdown Support**: Full markdown rendering in messages
✅ **Error Handling**: User-friendly error messages
✅ **Auto-scroll**: Automatically scrolls to new messages
✅ **Loading States**: Visual feedback during API calls

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

This will install:
- `react-router-dom` for routing between Green Agent and White Agent pages

### 2. Start the Backend

```bash
cd backend
python api_server.py
```

The API server will run on `http://localhost:8000`

### 3. Start the Frontend

```bash
cd frontend
npm run dev
```

The frontend will run on `http://localhost:5173`

## Navigation

The app now has two pages:

- **🌱 Green Agent** (`/`) - Full demo with evaluations, side panels, etc.
- **⚪ White Agent** (`/white-agent`) - Clean reasoning engine chat

## API Endpoints

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

## Components

### WhiteAgentChat (`/pages/WhiteAgentChat.tsx`)
Main chat interface for White Agent with:
- Clean, focused UI
- Agent type badges
- Real-time messaging
- Error handling

### Navigation (`/components/Navigation.tsx`)
Top navigation bar with tabs for switching between agents

## Styling

The White Agent page uses:
- **Purple theme** for White Agent messages
- **Blue theme** for user messages  
- **Green theme** for Supervisor messages
- **Orange theme** for Tool messages

All styling is done with Tailwind CSS for consistency with the rest of the app.

## Development

The White Agent page is designed to be:
1. **Simple** - Focus on chat, no complex side panels
2. **Fast** - Direct API calls, minimal overhead
3. **Clear** - Easy to see what each agent is doing
4. **Extensible** - Easy to add new features

## Next Steps

Potential enhancements:
- [ ] Add streaming support for real-time responses
- [ ] Show reasoning steps inline
- [ ] Add tool call visualization
- [ ] Export conversation history
- [ ] Add voice input


