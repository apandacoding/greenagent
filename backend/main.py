"""
FastAPI backend for Green Agent chatbot with flight booking functionality.
"""
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from chatbot.agent import GreenAgent
from chatbot.models import ChatMessage, ChatResponse, AgentStatus
from chatbot.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Green Agent API",
    description="AI Agent for flight booking and logistics",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="../"), name="static")

# Initialize the Green Agent
green_agent = GreenAgent()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await self.send_personal_message(message, connection)

manager = ConnectionManager()

@app.get("/")
async def root():
    """Root endpoint - serve the main page"""
    return {"message": "Green Agent API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_status": green_agent.get_status()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Main chat endpoint for processing user messages"""
    try:
        logger.info(f"Received message: {message.content}")
        
        # Process message through Green Agent
        response = await green_agent.process_message(message.content)
        
        return ChatResponse(
            message=response["message"],
            agent_type=response["agent_type"],
            tool_calls=response.get("tool_calls", []),
            status="success"
        )
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/status")
async def get_agent_status():
    """Get current agent status"""
    return green_agent.get_status()

@app.post("/agent/reset")
async def reset_agent():
    """Reset agent conversation history"""
    green_agent.reset()
    return {"message": "Agent reset successfully"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            logger.info(f"WebSocket message received: {message_data}")
            
            # Process through Green Agent
            response = await green_agent.process_message(message_data["message"])
            
            # Send response back to client
            response_data = {
                "message": response["message"],
                "agent_type": response["agent_type"],
                "tool_calls": response.get("tool_calls", []),
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_personal_message(
                json.dumps(response_data), 
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
