# GreenAgent Frontend

Clean, minimal chat interface for GreenAgent built with React, TypeScript, and TailwindCSS.

## 🚀 Quick Start

### Install Dependencies
```bash
npm install
```

### Development Server
```bash
npm run dev
```
The app will be available at `http://localhost:5173`

### Production Build
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## 🏗️ Architecture

### Components
- **ChatContainer** - Main container with header, messages, and input
- **ChatMessage** - Individual message bubble with markdown rendering
- **ChatInput** - Input field with send button
- **LoadingDots** - Typing indicator animation

### Hooks
- **useWebSocket** - WebSocket connection management and message handling

### Types
- **Message** - Message interface (id, role, content, timestamp)
- **WebSocketMessage** - WebSocket message protocol

## 🔌 Backend Connection

The frontend connects to the backend WebSocket at:
```
ws://localhost:8000/ws
```

Make sure the backend server is running before starting the frontend.

## 🎨 Design Principles

- **Minimal Viable UI/UX** - Only essential features
- **Clean & Simple** - No unnecessary animations or elements
- **Mobile-First** - Responsive design from the start
- **Claude-Inspired** - Centered conversation layout

## 📦 Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **TailwindCSS v4** - Styling
- **Vite** - Build tool
- **React-Markdown** - Message formatting

## 🌱 Features

- Real-time WebSocket communication
- Markdown message rendering
- Auto-scroll to latest message
- Connection status indicator
- Loading states
- Clean, minimal design
